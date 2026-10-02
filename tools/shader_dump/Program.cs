// shader_dump — Splatoon 3 셰이더 컨테이너(BFSHA/BNSH/SHARCB) 덤프 + Maxwell SASS -> GLSL 역번역
// 파서: KillzXGaming/ShaderLibrary (web/tools/shader_ryujinx/ShaderLibrary, commit 790dd2e)
// 역번역: Ryujinx.Graphics.Shader (ShaderLibrary.CompileTool/Libs 동봉 빌드, net7)
//
// 명령
//   info-bfsha  <x.bfsha> <out.json>
//   keys-bfsha  <x.bfsha> <model> <out.tsv>                         모든 프로그램의 옵션 선택값
//   prog-bfsha  <x.bfsha> <model> <options.json|-> <outprefix> [--index N]
//   info-sharc  <x.sharcb> <out.json>
//   prog-sharc  <x.sharcb> <program> <outdir>                      모든 변형(매크로 조합)
//   bnsh        <x.bnsh> <outdir>                                  모든 변형
using System.Globalization;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Ryujinx.Graphics.Shader;
using Ryujinx.Graphics.Shader.Translation;
using ShaderLibrary;
using ShaderLibrary.Helpers;

static class P
{
    static readonly JsonSerializerOptions JO = new() { WriteIndented = true, Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping };

    static int Main(string[] a)
    {
        CultureInfo.DefaultThreadCurrentCulture = CultureInfo.InvariantCulture;
        CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
        if (a.Length < 2) { Console.Error.WriteLine("usage: see header"); return 1; }
        switch (a[0])
        {
            case "info-bfsha": InfoBfsha(a[1], a[2]); break;
            case "keys-bfsha": KeysBfsha(a[1], a[2], a[3]); break;
            case "prog-bfsha": ProgBfsha(a[1], a[2], a[3], a[4], a.Length > 6 && a[5] == "--index" ? int.Parse(a[6]) : -1); break;
            case "info-sharc": InfoSharc(a[1], a[2]); break;
            case "prog-sharc": ProgSharc(a[1], a[2], a[3]); break;
            case "bnsh": Bnsh(a[1], a[2]); break;
            default: Console.Error.WriteLine("unknown cmd"); return 1;
        }
        return 0;
    }

    // ---------------- BFSHA ----------------
    static ShaderModel Model(BfshaFile f, string m) => int.TryParse(m, out int i) ? f.ShaderModels[i] : f.ShaderModels[m];

    static List<(string name, int off, int size)> UniformLayout(BfshaUniformBlock b)
    {
        var list = new List<(string, int, int)>();
        foreach (var kv in b.Uniforms)
        {
            int off = kv.Value.DataOffset == 0 ? -1 : kv.Value.DataOffset - 1;
            list.Add((kv.Key, off, 0));
        }
        var sorted = list.Where(x => x.Item2 >= 0).OrderBy(x => x.Item2).ToList();
        var res = new List<(string, int, int)>();
        for (int i = 0; i < sorted.Count; i++)
        {
            int end = i + 1 < sorted.Count ? sorted[i + 1].Item2 : b.Size;
            res.Add((sorted[i].Item1, sorted[i].Item2, end - sorted[i].Item2));
        }
        foreach (var x in list.Where(x => x.Item2 < 0)) res.Add((x.Item1, -1, 0));
        return res;
    }

    static void InfoBfsha(string path, string outp)
    {
        var f = new BfshaFile(path);
        var root = new Dictionary<string, object>
        {
            ["name"] = f.Name,
            ["version"] = $"{f.BinHeader.VersionMajor}.{f.BinHeader.VersionMinor}.{f.BinHeader.VersionMicro}",
        };
        var models = new List<object>();
        foreach (var mkv in f.ShaderModels)
        {
            var m = mkv.Value;
            Func<ResDict<ShaderOption>, object> opts = d => d.Select(o => new Dictionary<string, object>
            {
                ["name"] = o.Key,
                ["default"] = o.Value.DefaultChoice,
                ["defaultIdx"] = o.Value.DefaultChoiceIdx,
                ["choices"] = o.Value.Choices.Keys.ToList(),
                ["choiceValues"] = o.Value.ChoiceValues,
                ["bit32Index"] = o.Value.Bit32Index,
                ["bit32Shift"] = o.Value.Bit32Shift,
                ["bit32Mask"] = o.Value.Bit32Mask,
                ["blockOffset"] = o.Value.BlockOffset,
                ["keyOffset"] = o.Value.KeyOffset,
            }).ToList();
            var sym = m.SymbolData;
            var samplers = m.Samplers.Select((s, i) => new Dictionary<string, object>
            {
                ["name"] = s.Key,
                ["index"] = s.Value.Index,
                ["annotation"] = s.Value.Annotation,
                ["symbol"] = sym != null && s.Value.Index < sym.Samplers.Count ? sym.Samplers[s.Value.Index].Name1 : null,
            }).ToList();
            var blocks = m.UniformBlocks.Select(b =>
            {
                var lay = UniformLayout(b.Value);
                var def = b.Value.DefaultBuffer;
                return new Dictionary<string, object>
                {
                    ["name"] = b.Key,
                    ["index"] = b.Value.Index,
                    ["type"] = b.Value.Type.ToString(),
                    ["size"] = b.Value.Size,
                    ["symbol"] = sym != null && b.Value.Index < sym.UniformBlocks.Count ? sym.UniformBlocks[b.Value.Index].Name1 : null,
                    ["uniforms"] = lay.Select(u => new Dictionary<string, object>
                    {
                        ["name"] = u.name,
                        ["offset"] = u.off,
                        ["size"] = u.size,
                        ["default"] = (def != null && u.off >= 0 && u.size > 0 && u.off + u.size <= def.Length)
                            ? Enumerable.Range(0, u.size / 4).Select(k => (object)Fmt(BitConverter.ToSingle(def, u.off + k * 4))).ToList() : null,
                    }).ToList(),
                };
            }).ToList();
            models.Add(new Dictionary<string, object>
            {
                ["name"] = mkv.Key,
                ["numPrograms"] = m.Programs.Count,
                ["defaultProgramIndex"] = m.DefaultProgramIndex,
                ["staticKeyLength"] = m.StaticKeyLength,
                ["dynamicKeyLength"] = m.DynamicKeyLength,
                ["blockIndices"] = m.BlockIndices,
                ["staticOptions"] = opts(m.StaticOptions),
                ["dynamicOptions"] = opts(m.DynamicOptions),
                ["attributes"] = m.Attributes.Select(x => new { name = x.Key, index = x.Value.Index, location = x.Value.Location }).ToList(),
                ["samplers"] = samplers,
                ["uniformBlocks"] = blocks,
                ["storageBuffers"] = m.StorageBuffers.Keys.ToList(),
                ["symbolSamplers"] = sym?.Samplers.Select(s => new[] { s.Name1, s.Value1, s.Name2, s.Value2, s.Name3, s.Value3 }).ToList(),
                ["symbolUniformBlocks"] = sym?.UniformBlocks.Select(s => new[] { s.Name1, s.Value1, s.Name2, s.Value2, s.Name3, s.Value3 }).ToList(),
                ["numBnshVariations"] = m.BnshFile?.Variations.Count ?? 0,
            });
        }
        root["models"] = models;
        File.WriteAllText(outp, JsonSerializer.Serialize(root, JO));
        Console.WriteLine($"wrote {outp}");
    }

    static string ChoiceOf(ShaderModel m, int prog, ShaderOption o, bool dyn)
    {
        int n = m.StaticKeyLength + m.DynamicKeyLength;
        int bas = n * prog;
        int key = dyn ? m.KeyTable[bas + m.StaticKeyLength + (o.Bit32Index - o.KeyOffset)] : m.KeyTable[bas + o.Bit32Index];
        int ci = o.GetChoiceIndex(key);
        return ci < 0 || ci >= o.Choices.Count ? $"?{ci}" : o.Choices.GetKey(ci);
    }

    static void KeysBfsha(string path, string model, string outp)
    {
        var f = new BfshaFile(path);
        var m = Model(f, model);
        using var w = new StreamWriter(outp);
        var so = m.StaticOptions.Values.ToList();
        var dy = m.DynamicOptions.Values.ToList();
        w.WriteLine("program\tvariation\t" + string.Join("\t", so.Select(o => o.Name)) + "\t" + string.Join("\t", dy.Select(o => "dyn:" + o.Name)));
        for (int p = 0; p < m.Programs.Count; p++)
            w.WriteLine($"{p}\t{m.Programs[p].VariationIndex}\t" + string.Join("\t", so.Select(o => ChoiceOf(m, p, o, false))) + "\t" + string.Join("\t", dy.Select(o => ChoiceOf(m, p, o, true))));
        Console.WriteLine($"wrote {outp} ({m.Programs.Count} programs)");
    }

    static void ProgBfsha(string path, string model, string optsPath, string outPrefix, int forced)
    {
        var f = new BfshaFile(path);
        var m = Model(f, model);
        var opts = optsPath == "-" ? new Dictionary<string, string>() : JsonSerializer.Deserialize<Dictionary<string, string>>(File.ReadAllText(optsPath));
        int prog = forced;
        if (prog < 0)
        {
            var list = m.GetProgramIndexList(opts);
            Console.WriteLine($"matching programs: {list.Count} [{string.Join(",", list.Take(20))}{(list.Count > 20 ? ",..." : "")}]");
            if (list.Count == 0) { Console.Error.WriteLine("no program"); return; }
            prog = list[0];
        }
        var sb = new StringBuilder();
        sb.AppendLine($"// program {prog} variation {m.Programs[prog].VariationIndex}");
        foreach (var o in m.StaticOptions.Values) sb.AppendLine($"//   {o.Name} = {ChoiceOf(m, prog, o, false)}{(ChoiceOf(m, prog, o, false) == o.DefaultChoice ? "" : "   (default " + o.DefaultChoice + ")")}");
        foreach (var o in m.DynamicOptions.Values) sb.AppendLine($"//   dyn {o.Name} = {ChoiceOf(m, prog, o, true)}");
        File.WriteAllText(outPrefix + ".options.txt", sb.ToString());

        var v = m.GetVariation(prog).BinaryProgram;
        // 유니폼 블록 심볼 -> 레이아웃
        var layouts = new Dictionary<string, List<(string, int, int)>>();
        foreach (var b in m.UniformBlocks)
        {
            string sym = m.SymbolData != null && b.Value.Index < m.SymbolData.UniformBlocks.Count ? m.SymbolData.UniformBlocks[b.Value.Index].Name1 : null;
            if (!string.IsNullOrEmpty(sym)) layouts[sym] = UniformLayout(b.Value);
        }
        var samplerNames = new Dictionary<string, string>();
        foreach (var s in m.Samplers)
        {
            string sym = m.SymbolData != null && s.Value.Index < m.SymbolData.Samplers.Count ? m.SymbolData.Samplers[s.Value.Index].Name1 : null;
            if (!string.IsNullOrEmpty(sym)) samplerNames[sym] = s.Key;
        }
        void Emit(BnshFile.ShaderCode code, BnshFile.ShaderReflectionData refl, string ext)
        {
            if (code == null) return;
            string glsl = Decompile(code.ByteCode, code.ControlCode, ReflRenames(refl), layouts);
            var hdr = new StringBuilder();
            hdr.AppendLine($"// {Path.GetFileName(path)} model {m.Name} program {prog} ({ext})");
            if (refl != null)
            {
                foreach (var kv in refl.Samplers) hdr.AppendLine($"// sampler {kv.Key} -> loc {refl.GetSamplerLocation(kv.Key)} -> material sampler {(samplerNames.TryGetValue(kv.Key, out var sn) ? sn : "?")}");
                foreach (var kv in refl.UniformBuffers) hdr.AppendLine($"// ubo {kv.Key} -> loc {refl.GetConstantBufferLocation(kv.Key)}{(layouts.ContainsKey(kv.Key) ? " (labelled)" : "")}");
                foreach (var kv in refl.Inputs) hdr.AppendLine($"// in {kv.Key} -> loc {refl.GetInputLocation(kv.Key)}");
                foreach (var kv in refl.Outputs) hdr.AppendLine($"// out {kv.Key} -> loc {refl.GetOutputLocation(kv.Key)}");
            }
            File.WriteAllText($"{outPrefix}.{ext}", hdr + glsl);
            Console.WriteLine($"wrote {outPrefix}.{ext}");
        }
        Emit(v.VertexShader, v.VertexShaderReflection, "vert");
        Emit(v.GeometryShader, v.GeometryShaderReflection, "geom");
        Emit(v.FragmentShader, v.FragmentShaderReflection, "frag");
        Emit(v.ComputeShader, v.ComputeShaderReflection, "comp");
    }

    static Dictionary<string, string> ReflRenames(BnshFile.ShaderReflectionData r)
    {
        var d = new Dictionary<string, string>();
        if (r == null) return d;
        foreach (var s in r.Samplers.Keys)
        {
            int loc = r.GetSamplerLocation(s);
            if (loc < 0) continue;
            string h = (loc * 2 + 8).ToString("X1");
            foreach (var st in new[] { "vp", "fp", "gp", "cp" }) d[$"{st}_t_tcb_{h}"] = s;
        }
        foreach (var s in r.UniformBuffers.Keys)
        {
            int loc = r.GetConstantBufferLocation(s);
            if (loc < 0) continue;
            foreach (var st in new[] { "vp", "fp", "gp", "cp" }) { d[$"_{st}_c{loc + 3}"] = "_" + s; d[$"{st}_c{loc + 3}"] = s; }
        }
        foreach (var s in r.Inputs.Keys) { int loc = r.GetInputLocation(s); if (loc >= 0) d[$"in_attr{loc}"] = s; }
        foreach (var s in r.Outputs.Keys) { int loc = r.GetOutputLocation(s); if (loc >= 0) d[$"out_attr{loc}"] = s; }
        return d;
    }

    // ---------------- 역번역 공통 ----------------
    static string Fmt(float v)
    {
        uint bits = BitConverter.SingleToUInt32Bits(v);
        if (float.IsNaN(v) || float.IsInfinity(v) || (v != 0 && Math.Abs(v) < 1e-30f) || Math.Abs(v) > 1e30f)
            return $"uintBitsToFloat(0x{bits:X8}u)";
        string s = v.ToString("R", CultureInfo.InvariantCulture);
        if (!s.Contains('.') && !s.Contains('E')) s += ".0";
        return s;
    }

    static string Decompile(byte[] byteCode, byte[] control, Dictionary<string, string> renames, Dictionary<string, List<(string, int, int)>> layouts)
    {
        string code;
        try
        {
            var data = byteCode.AsSpan(48).ToArray();
            var opt = new TranslationOptions(TargetLanguage.Glsl, TargetApi.OpenGL, TranslationFlags.None);
            code = Translator.CreateContext(0, new Acc(data), opt).Translate().Code;
        }
        catch (Exception e) { return "// TRANSLATE FAILED: " + e.Message + "\n"; }

        // c1 = 컨트롤 섹션이 가리키는 임베디드 상수
        float[] consts = new float[0];
        try { consts = new ShaderLibrary.CompileTool.ControlShader(control).GetConstantsAsFloats(byteCode); } catch { }
        code = Regex.Replace(code, @"\b(vp|fp|gp|cp)_c1\.data\[(\d+)\]\.([xyzw])", mm =>
        {
            int i = int.Parse(mm.Groups[2].Value) * 4 + "xyzw".IndexOf(mm.Groups[3].Value[0]);
            return i < consts.Length ? Fmt(consts[i]) : mm.Value;
        });
        foreach (var kv in renames.OrderByDescending(k => k.Key.Length))
            code = Regex.Replace(code, $@"\b{Regex.Escape(kv.Key)}\b", kv.Value);
        if (layouts != null)
            foreach (var lay in layouts)
            {
                var flat = new Dictionary<int, string>();
                foreach (var (name, off, size) in lay.Value)
                {
                    if (off < 0 || size <= 0) continue;
                    int n = size / 4;
                    for (int k = 0; k < n; k++)
                    {
                        string lab = n == 1 ? name : n <= 4 ? $"{name}.{"xyzw"[k]}" : $"{name}[{k / 4}].{"xyzw"[k % 4]}";
                        flat[off / 4 + k] = lab;
                    }
                }
                code = Regex.Replace(code, $@"\b{Regex.Escape(lay.Key)}\.data\[(\d+)\]\.([xyzw])", mm =>
                {
                    int i = int.Parse(mm.Groups[1].Value) * 4 + "xyzw".IndexOf(mm.Groups[2].Value[0]);
                    return flat.TryGetValue(i, out var lab) ? $"{lay.Key}.{lab}" : mm.Value;
                });
            }
        return code;
    }

    class Acc : IGpuAccessor
    {
        readonly byte[] d;
        public Acc(byte[] data) { d = data; }
        public ReadOnlySpan<ulong> GetCode(ulong address, int minimumSize) => MemoryMarshal.Cast<byte, ulong>(new ReadOnlySpan<byte>(d).Slice((int)address));
    }

    // ---------------- SHARCB ----------------
    static void InfoSharc(string path, string outp)
    {
        var f = new SharcfbFile(path);
        var root = new Dictionary<string, object>
        {
            ["name"] = f.Name,
            ["version"] = f.FileHeader.Version,
            ["numVariations"] = f.Variations.Count,
            ["programs"] = f.Programs.Select(p => new Dictionary<string, object>
            {
                ["name"] = p.Name,
                ["kind"] = p.Kind,
                ["baseIndex"] = p.BaseIndex,
                ["macros"] = p.VariationMacros.Select(v => new { name = v.Name, values = v.Values }).ToList(),
            }).ToList(),
        };
        File.WriteAllText(outp, JsonSerializer.Serialize(root, JO));
        Console.WriteLine($"wrote {outp}");
    }

    static Dictionary<string, string> SharcRenames(SharcfbFile.ShaderVariation v)
    {
        var d = new Dictionary<string, string>();
        foreach (var s in v.Samplers)
        {
            string h = (s.Location * 2 + 8).ToString("X1");
            foreach (var st in new[] { "vp", "fp", "gp", "cp" }) d[$"{st}_t_tcb_{h}"] = s.Name;
        }
        foreach (var b in v.UniformBlocks)
            foreach (var st in new[] { "vp", "fp", "gp", "cp" }) { d[$"_{st}_c{b.Location + 3}"] = "_" + b.Name; d[$"{st}_c{b.Location + 3}"] = b.Name; }
        foreach (var a in v.Attributes) d[$"in_attr{a.Location}"] = a.Name;
        return d;
    }

    static void ProgSharc(string path, string progName, string outdir)
    {
        var f = new SharcfbFile(path);
        Directory.CreateDirectory(outdir);
        foreach (var p in f.Programs.Where(p => progName == "*" || p.Name == progName))
        {
            var combos = p.GetAllVariationCombinations().ToList();
            int stages = p.HasGeometryShader() ? 3 : 2;
            for (int ci = 0; ci < combos.Count; ci++)
            {
                var combo = combos[ci];
                string tag = string.Join("_", combo.Select(kv => $"{kv.Key}-{kv.Value}"));
                if (tag.Length == 0) tag = "default";
                int bi = p.BaseIndex + ci * stages;
                for (int s = 0; s < stages; s++)
                {
                    if (bi + s >= f.Variations.Count) break;
                    var v = f.Variations[bi + s];
                    string ext = v.Type.ToString().ToLowerInvariant();
                    var hdr = new StringBuilder();
                    hdr.AppendLine($"// {Path.GetFileName(path)} program {p.Name} variation#{ci} binary {bi + s} type {v.Type}");
                    foreach (var kv in combo) hdr.AppendLine($"//   #define {kv.Key} {kv.Value}");
                    foreach (var x in v.UniformBlocks) hdr.AppendLine($"// ubo {x.Name} loc {x.Location} size {x.Size}");
                    foreach (var x in v.Uniforms) hdr.AppendLine($"// uniform {x.Name} loc {x.Location}");
                    foreach (var x in v.Samplers) hdr.AppendLine($"// sampler {x.Name} loc {x.Location}");
                    foreach (var x in v.Attributes) hdr.AppendLine($"// attr {x.Name} loc {x.Location}");
                    foreach (var x in v.Buffers) hdr.AppendLine($"// buffer {x.Name} loc {x.Location}");
                    var slay = new Dictionary<string, List<(string, int, int)>>();
                    var ub = v.UniformBlocks.FirstOrDefault();
                    if (ub != null && v.Uniforms.Count > 0)
                    {
                        var us = v.Uniforms.OrderBy(x => x.Location).ToList();
                        slay[ub.Name] = us.Select((x, k) => (x.Name.Replace("[0]", ""), x.Location, (k + 1 < us.Count ? us[k + 1].Location : (int)ub.Size) - x.Location)).ToList();
                    }
                    string glsl = v.ByteCode == null || v.ByteCode.Length < 0x30 ? "// (no code)\n" : Decompile(v.ByteCode, v.ControlShader, SharcRenames(v), slay);
                    string fn = Path.Combine(outdir, $"{p.Name}__{tag}.{ext}.glsl");
                    File.WriteAllText(fn, hdr + glsl);
                }
            }
            Console.WriteLine($"{p.Name}: {combos.Count} combos");
        }
    }

    // ---------------- BNSH ----------------
    static void Bnsh(string path, string outdir)
    {
        var f = new BnshFile(path);
        Directory.CreateDirectory(outdir);
        for (int i = 0; i < f.Variations.Count; i++)
        {
            var v = f.Variations[i].BinaryProgram;
            void Emit(BnshFile.ShaderCode code, BnshFile.ShaderReflectionData refl, string ext)
            {
                if (code == null) return;
                var hdr = new StringBuilder($"// {Path.GetFileName(path)} variation {i} ({ext})\n");
                if (refl != null)
                {
                    foreach (var kv in refl.Samplers) hdr.AppendLine($"// sampler {kv.Key} loc {refl.GetSamplerLocation(kv.Key)}");
                    foreach (var kv in refl.UniformBuffers) hdr.AppendLine($"// ubo {kv.Key} loc {refl.GetConstantBufferLocation(kv.Key)}");
                    foreach (var kv in refl.Inputs) hdr.AppendLine($"// in {kv.Key} loc {refl.GetInputLocation(kv.Key)}");
                    foreach (var kv in refl.Outputs) hdr.AppendLine($"// out {kv.Key} loc {refl.GetOutputLocation(kv.Key)}");
                }
                File.WriteAllText(Path.Combine(outdir, $"var{i:D3}.{ext}.glsl"), hdr + Decompile(code.ByteCode, code.ControlCode, ReflRenames(refl), null));
            }
            Emit(v.VertexShader, v.VertexShaderReflection, "vert");
            Emit(v.GeometryShader, v.GeometryShaderReflection, "geom");
            Emit(v.FragmentShader, v.FragmentShaderReflection, "frag");
            Emit(v.ComputeShader, v.ComputeShaderReflection, "comp");
        }
        Console.WriteLine($"{f.Variations.Count} variations -> {outdir}");
    }
}
