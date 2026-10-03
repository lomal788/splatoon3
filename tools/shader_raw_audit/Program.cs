// Raw original stage audit. Dumps bytes without modification; no native GPU execution.
using ShaderLibrary;
using System.Reflection;
using System.Text.Json;
class P {
 static void Main(string[] a) {
 var asm=typeof(Ryujinx.Graphics.Shader.Translation.Translator).Assembly;
 if(a[0]=="types") { foreach(var t in asm.GetTypes().Where(t=>t.FullName.Contains(a[1]))) {
 Console.WriteLine(t.FullName);foreach(var m in t.GetMethods(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static|BindingFlags.Instance|BindingFlags.DeclaredOnly))Console.WriteLine("  "+m);foreach(var p in t.GetProperties())Console.WriteLine("  PROP "+p);foreach(var f in t.GetFields(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.Static))Console.WriteLine("  FIELD "+f); } return; }
 if(a[0]=="ops") {
 var d=File.ReadAllBytes(a[1]);var ct=File.ReadAllBytes(a[1].Replace(".bin",".control"));int len=(int)BitConverter.ToUInt32(ct,1784);var tb=asm.GetType("Ryujinx.Graphics.Shader.Decoders.InstTable");var get=tb.GetMethod("GetOp",BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static);
 for(int off=0x50;off<len;off+=8){if((off-0x50)%32==0)continue;ulong raw=BitConverter.ToUInt64(d,48+off);object op=get.Invoke(null,new object[]{(ulong)off,raw});var typ=op.GetType();string name=typ.GetField("Name").GetValue(op).ToString();string extra="";
 if(name=="Ast"||name=="Ipa"||name=="Ald") {var it=asm.GetType("Ryujinx.Graphics.Shader.Decoders.Inst"+name);object ins=Activator.CreateInstance(it,BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic,null,new object[]{raw},null);extra=string.Join(" ",it.GetProperties().Select(p=>p.Name+"="+p.GetValue(ins)));}
 Console.WriteLine($"{off:x4}\t{raw:x16}\t{name}\t{extra}");}return;
 }
 var bf=new BfshaFile(a[0]);var model=bf.ShaderModels[a[1]];int pi=int.Parse(a[2]);var v=model.GetVariation(pi).BinaryProgram;var rows=new List<object>();
 void Stage(BnshFile.ShaderCode c,BnshFile.ShaderReflectionData r,string name){if(c==null)return;File.WriteAllBytes(a[3]+"."+name+".bin",c.ByteCode);File.WriteAllBytes(a[3]+"."+name+".control",c.ControlCode);rows.Add(new {stage=name,bytes=c.ByteCode.Length,controlBytes=c.ControlCode.Length,shaderHeaderU32=Enumerable.Range(0,20).Select(i=>BitConverter.ToUInt32(c.ByteCode,48+4*i).ToString("x8")).ToArray(),inputs=r?.Inputs.Select(x=>new {name=x.Key,location=r.GetInputLocation(x.Key)}).ToArray(),outputs=r?.Outputs.Select(x=>new {name=x.Key,location=r.GetOutputLocation(x.Key)}).ToArray(),ubos=r?.UniformBuffers.Select(x=>new {name=x.Key,location=r.GetConstantBufferLocation(x.Key)}).ToArray()});}
 Stage(v.VertexShader,v.VertexShaderReflection,"vert");Stage(v.GeometryShader,v.GeometryShaderReflection,"geom");Stage(v.FragmentShader,v.FragmentShaderReflection,"frag");
 File.WriteAllText(a[3]+".raw.json",JsonSerializer.Serialize(new {program=pi,variation=model.Programs[pi].VariationIndex,stages=rows},new JsonSerializerOptions{WriteIndented=true}));Console.WriteLine($"program {pi} stages {rows.Count}");
 }
}


