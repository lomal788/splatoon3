// Hoian_UBER.Product.bfsha model hoian_uber program 917 (frag)
// sampler cEnvBRDFMap -> loc 24 -> material sampler ?
// sampler cGSysProjection0 -> loc 16 -> material sampler gsys_projection0
// sampler cGSysShadowPrePass -> loc 17 -> material sampler gsys_shadow_prepass
// sampler cPrefilEnvMapArray -> loc 23 -> material sampler ?
// sampler cTexAlbedo -> loc 1 -> material sampler _a0
// sampler cTexBakeAOShadow -> loc 10 -> material sampler _b0
// sampler cTexBakeLight -> loc 11 -> material sampler _b1
// sampler cTexNormal -> loc 3 -> material sampler _n0
// sampler cTexRoughness -> loc 4 -> material sampler _r0
// ubo BlitzUBO0 -> loc 4 (labelled)
// ubo BlitzUBO2 -> loc 6 (labelled)
// ubo Context -> loc 0 (labelled)
// ubo Env -> loc 2 (labelled)
// ubo Mat -> loc 3 (labelled)
// out output_color[0] -> loc 0
#version 450 core
#extension GL_ARB_gpu_shader_int64 : enable
#extension GL_ARB_shader_ballot : enable
#extension GL_ARB_shader_group_vote : enable
#extension GL_EXT_shader_image_load_formatted : enable
#extension GL_EXT_texture_shadow_lod : enable
#extension GL_ARB_fragment_shader_interlock : enable
#extension GL_NV_viewport_array2 : enable
#pragma optionNV(fastmath off)

const int undef = 0;

layout (binding = 0, std140) uniform _support_buffer
{
    uint alpha_test;
    uint is_bgra[8];
    precise vec4 viewport_inverse;
    precise vec4 viewport_size;
    int frag_scale_count;
    precise float render_scale[73];
    ivec4 tfe_offset;
    int tfe_vertex_count;
} support_buffer;

layout (binding = 9, std140) uniform _BlitzUBO2
{
    precise vec4 data[4096];
} BlitzUBO2;

layout (binding = 1, std140) uniform _fp_c1
{
    precise vec4 data[4096];
} fp_c1;

layout (binding = 5, std140) uniform _Env
{
    precise vec4 data[4096];
} Env;

layout (binding = 3, std140) uniform _Context
{
    precise vec4 data[4096];
} Context;

layout (binding = 6, std140) uniform _Mat
{
    precise vec4 data[4096];
} Mat;

layout (binding = 7, std140) uniform _BlitzUBO0
{
    precise vec4 data[4096];
} BlitzUBO0;

layout (binding = 0) uniform sampler2D cTexNormal;
layout (binding = 1) uniform sampler2D cTexRoughness;
layout (binding = 2) uniform sampler2D cGSysShadowPrePass;
layout (binding = 3) uniform sampler2D cTexAlbedo;
layout (binding = 4) uniform sampler2D cGSysProjection0;
layout (binding = 5) uniform sampler2D cEnvBRDFMap;
layout (binding = 6) uniform samplerCubeArray cPrefilEnvMapArray;
layout (binding = 7) uniform sampler2D cTexBakeAOShadow;
layout (binding = 8) uniform sampler2D cTexBakeLight;
layout (location = 0) in vec4 in_attr0;
layout (location = 1) in vec4 in_attr1;
layout (location = 2) in vec4 in_attr2;
layout (location = 3) in vec4 in_attr3;
layout (location = 4) in vec4 in_attr4;
layout (location = 5) in vec4 in_attr5;
layout (location = 6) in vec4 in_attr6;
layout (location = 7) in vec4 in_attr7;

layout (location = 0) out vec4 output_color[0];


void main()
{
    precise float temp_0;
    precise float temp_1;
    precise float temp_2;
    precise float temp_3;
    precise vec2 temp_4;
    precise float temp_5;
    precise float temp_6;
    precise vec2 temp_7;
    precise vec3 temp_8;
    precise float temp_9;
    precise float temp_10;
    precise float temp_11;
    precise float temp_12;
    precise float temp_13;
    precise float temp_14;
    precise float temp_15;
    precise float temp_16;
    precise float temp_17;
    precise float temp_18;
    precise float temp_19;
    precise float temp_20;
    precise float temp_21;
    precise float temp_22;
    precise float temp_23;
    precise float temp_24;
    precise float temp_25;
    precise float temp_26;
    precise float temp_27;
    precise float temp_28;
    precise float temp_29;
    precise float temp_30;
    precise float temp_31;
    precise float temp_32;
    precise float temp_33;
    precise float temp_34;
    precise float temp_35;
    precise float temp_36;
    precise float temp_37;
    precise float temp_38;
    precise float temp_39;
    precise float temp_40;
    precise float temp_41;
    precise float temp_42;
    precise float temp_43;
    precise float temp_44;
    precise vec2 temp_45;
    precise float temp_46;
    precise float temp_47;
    precise vec3 temp_48;
    precise vec2 temp_49;
    precise vec4 temp_50;
    precise float temp_51;
    precise float temp_52;
    precise float temp_53;
    precise float temp_54;
    precise float temp_55;
    precise float temp_56;
    precise float temp_57;
    precise float temp_58;
    precise float temp_59;
    precise float temp_60;
    precise float temp_61;
    precise float temp_62;
    precise float temp_63;
    precise float temp_64;
    precise float temp_65;
    precise float temp_66;
    precise float temp_67;
    precise float temp_68;
    precise float temp_69;
    precise float temp_70;
    precise float temp_71;
    precise float temp_72;
    precise float temp_73;
    precise float temp_74;
    precise float temp_75;
    precise float temp_76;
    precise float temp_77;
    uint temp_78;
    precise float temp_79;
    precise float temp_80;
    precise float temp_81;
    precise float temp_82;
    precise float temp_83;
    precise float temp_84;
    precise float temp_85;
    precise float temp_86;
    precise float temp_87;
    precise float temp_88;
    precise float temp_89;
    precise float temp_90;
    precise float temp_91;
    precise float temp_92;
    precise float temp_93;
    precise float temp_94;
    precise float temp_95;
    precise float temp_96;
    precise float temp_97;
    precise float temp_98;
    precise float temp_99;
    precise float temp_100;
    precise float temp_101;
    precise float temp_102;
    int temp_103;
    int temp_104;
    int temp_105;
    precise float temp_106;
    precise float temp_107;
    precise float temp_108;
    int temp_109;
    bool temp_110;
    int temp_111;
    uint temp_112;
    int temp_113;
    uint temp_114;
    precise float temp_115;
    precise float temp_116;
    precise float temp_117;
    precise float temp_118;
    precise float temp_119;
    precise float temp_120;
    precise float temp_121;
    precise float temp_122;
    precise float temp_123;
    precise float temp_124;
    uint temp_125;
    int temp_126;
    precise float temp_127;
    precise float temp_128;
    precise float temp_129;
    precise float temp_130;
    precise float temp_131;
    precise float temp_132;
    precise float temp_133;
    uint temp_134;
    precise float temp_135;
    uint temp_136;
    precise float temp_137;
    uint temp_138;
    int temp_139;
    precise float temp_140;
    precise float temp_141;
    bool temp_142;
    precise float temp_143;
    precise float temp_144;
    uint temp_145;
    int temp_146;
    uint temp_147;
    uint temp_148;
    precise float temp_149;
    int temp_150;
    int temp_151;
    precise float temp_152;
    precise float temp_153;
    precise float temp_154;
    precise float temp_155;
    precise float temp_156;
    precise float temp_157;
    precise float temp_158;
    precise float temp_159;
    precise float temp_160;
    precise float temp_161;
    precise float temp_162;
    precise float temp_163;
    precise float temp_164;
    precise float temp_165;
    precise float temp_166;
    precise float temp_167;
    precise float temp_168;
    precise float temp_169;
    precise float temp_170;
    temp_110 = false;
    temp_0 = 1.0 / (in_attr6.z * gl_FragCoord.w);
    temp_1 = in_attr0.x;
    temp_2 = in_attr0.y;
    temp_3 = 1.0 / in_attr5.w;
    temp_4 = texture(cTexNormal, vec2(temp_1, temp_2)).xy;
    temp_5 = temp_4.x;
    temp_6 = temp_4.y;
    temp_7 = texture(cGSysShadowPrePass, vec2(fma(in_attr5.x * temp_3, 0.5, 0.5), fma(in_attr5.y * temp_3, -0.5, 0.5))).xy;
    temp_8 = texture(cTexAlbedo, vec2(temp_1, temp_2)).xyz;
    temp_9 = temp_8.x;
    temp_10 = temp_8.y;
    temp_11 = temp_8.z;
    temp_12 = in_attr1.x;
    temp_13 = in_attr1.y;
    temp_14 = in_attr1.z;
    temp_15 = in_attr2.y;
    temp_16 = in_attr2.z;
    temp_17 = in_attr2.x;
    temp_18 = in_attr2.w;
    temp_19 = in_attr4.x;
    temp_20 = in_attr4.y;
    temp_21 = in_attr4.z;
    temp_22 = inversesqrt(fma(temp_14, temp_14, fma(temp_13, temp_13, temp_12 * temp_12)));
    temp_23 = temp_14 * temp_22;
    temp_24 = temp_12 * temp_22;
    temp_25 = temp_13 * temp_22;
    temp_26 = max(texture(cTexRoughness, vec2(temp_1, temp_2)).x, 0.0001);
    temp_27 = sqrt(clamp((0.0 - fma(temp_5, temp_5, temp_6 * temp_6)) + 1.0, 0.0, 1.0));
    temp_28 = fma(temp_24, temp_27, fma(temp_5, temp_17, temp_6 * fma(temp_25, temp_16, (0.0 - temp_23 * temp_15)) * temp_18));
    temp_29 = fma(temp_25, temp_27, fma(temp_5, temp_15, temp_6 * fma(temp_23, temp_17, (0.0 - temp_24 * temp_16)) * temp_18));
    temp_30 = fma(temp_23, temp_27, fma(temp_5, temp_16, temp_6 * fma(temp_24, temp_15, (0.0 - temp_25 * temp_17)) * temp_18));
    temp_31 = inversesqrt(fma(temp_21, temp_21, fma(temp_20, temp_20, temp_19 * temp_19)));
    temp_32 = temp_19 * (0.0 - temp_31);
    temp_33 = inversesqrt(fma(temp_30, temp_30, fma(temp_29, temp_29, temp_28 * temp_28)));
    temp_34 = temp_20 * (0.0 - temp_31);
    temp_35 = temp_21 * (0.0 - temp_31);
    temp_36 = temp_28 * temp_33;
    temp_37 = temp_29 * temp_33;
    temp_38 = temp_30 * temp_33;
    temp_39 = fma(temp_38, temp_35, fma(temp_37, temp_34, temp_36 * temp_32));
    temp_40 = max(temp_39, 1E-08);
    temp_41 = fma(temp_37 * (0.0 - temp_39), -2.0, (0.0 - temp_34));
    temp_42 = fma(temp_36 * (0.0 - temp_39), -2.0, (0.0 - temp_32));
    temp_43 = fma(temp_38 * (0.0 - temp_39), -2.0, (0.0 - temp_35));
    temp_44 = 1.0 / max(abs(temp_43), max(abs(temp_42), abs(temp_41)));
    temp_45 = texture(cEnvBRDFMap, vec2(temp_40, (0.0 - temp_26) + -0.0)).xy;
    temp_46 = temp_45.x;
    temp_47 = temp_45.y;
    temp_48 = texture(cPrefilEnvMapArray, vec4(temp_42 * temp_44, temp_41 * temp_44, temp_43 * temp_44, float(int(clamp(uint(max(roundEven(roundEven(fma(cos(temp_26 * 3.14159274), -5.5, 5.5))), 0.0)), 0u, 0xFFFFu))))).xyz;
    temp_49 = texture(cTexBakeAOShadow, vec2(in_attr7.x, in_attr7.y)).xy;
    temp_50 = texture(cTexBakeLight, vec2(in_attr7.z, in_attr7.w)).xyzw;
    temp_51 = temp_50.w;
    temp_52 = temp_32 + (0.0 - Env.data[23].x);
    temp_53 = in_attr3.x;
    temp_54 = temp_34 + (0.0 - Env.data[23].y);
    temp_55 = in_attr3.z;
    temp_56 = temp_35 + (0.0 - Env.data[23].z);
    temp_57 = temp_38 * temp_38;
    temp_58 = temp_36 * temp_37;
    temp_59 = temp_37 * temp_38;
    temp_60 = inversesqrt(fma(temp_56, temp_56, fma(temp_54, temp_54, temp_52 * temp_52)));
    temp_61 = temp_52 * temp_60;
    temp_62 = temp_54 * temp_60;
    temp_63 = temp_56 * temp_60;
    temp_64 = temp_36 * temp_38;
    temp_65 = fma(temp_36, temp_36, (0.0 - temp_37 * temp_37));
    temp_66 = temp_26 * temp_26;
    temp_67 = fma(temp_37, (0.0 - Env.data[23].y), temp_36 * (0.0 - Env.data[23].x));
    temp_68 = max(fma(temp_38, temp_63, fma(temp_37, temp_62, temp_36 * temp_61)), 1E-08) * max(fma(temp_38, temp_63, fma(temp_37, temp_62, temp_36 * temp_61)), 1E-08);
    temp_69 = fma(temp_26, 0.5, 0.5);
    temp_70 = temp_69 * 0.5 * temp_69;
    temp_71 = max(fma(temp_35, temp_63, fma(temp_34, temp_62, temp_32 * temp_61)), 1E-08);
    temp_72 = max(fma(temp_38, (0.0 - Env.data[23].z), temp_67), 1E-08);
    temp_73 = 1.0 / (temp_70 + fma(temp_40, (0.0 - temp_70), temp_40));
    temp_74 = exp2(temp_71 * fma(temp_71, -5.55473, -6.98316002));
    temp_75 = fma(temp_10 + -0.0399999991, Mat.metalness, 0.0399999991);
    temp_76 = fma(temp_10, (0.0 - Mat.metalness), temp_10);
    temp_77 = fma(temp_9 + -0.0399999991, Mat.metalness, 0.0399999991);
    temp_78 = uint(max(0, min(int(trunc((temp_55 + (0.0 - BlitzUBO2.data[0x226].z)) * BlitzUBO2.data[0x227].z)), 19)) * 20 + max(0, min(int(trunc((temp_53 + (0.0 - BlitzUBO2.data[0x226].x)) * BlitzUBO2.data[0x227].x)), 19)) << 4) >> 2;
    temp_79 = BlitzUBO2.data[int(temp_78 >> 2)][int(temp_78) & 3];
    temp_80 = fma(temp_11 + -0.0399999991, Mat.metalness, 0.0399999991);
    temp_81 = fma(temp_9, (0.0 - Mat.metalness), temp_9);
    temp_82 = fma(temp_77, (0.0 - temp_81), temp_81);
    temp_83 = temp_73 * (1.0 / (temp_70 + fma(temp_70, (0.0 - temp_72), temp_72))) * temp_66 * (1.0 / max(fma(temp_68, temp_66 * temp_66, (0.0 - temp_68)) + 1.0, 1E-08)) * temp_66 * (1.0 / max(fma(temp_68, temp_66 * temp_66, (0.0 - temp_68)) + 1.0, 1E-08));
    temp_84 = fma(temp_11, (0.0 - Mat.metalness), temp_11);
    temp_85 = fma(temp_75, (0.0 - temp_76), temp_76);
    temp_86 = fma(temp_80, (0.0 - temp_84), temp_84);
    temp_87 = temp_50.y * temp_51 * 32.0;
    temp_88 = temp_50.x * temp_51 * 32.0;
    temp_89 = temp_50.z * temp_51 * 32.0;
    temp_90 = fma(temp_82, temp_88, fma(temp_48.x, fma(temp_77, temp_46, temp_47), temp_82 * max(0.0, fma(temp_65, Env.data[31].x, fma(temp_38, Env.data[25].z, fma(temp_37, Env.data[25].y, temp_36 * Env.data[25].x)) + Env.data[25].w + fma(temp_64, Env.data[28].w, fma(temp_57, Env.data[28].z, fma(temp_59, Env.data[28].y, temp_58 * Env.data[28].x)))))));
    temp_91 = clamp(fma(temp_49.x, (0.0 - BlitzUBO0.data[37].x), BlitzUBO0.data[37].x) + BlitzUBO0.data[37].y, 0.0, 1.0);
    temp_92 = clamp(fma(temp_38, (0.0 - Env.data[23].z), temp_67), 0.0, 1.0);
    temp_93 = fma(temp_86, temp_89, fma(temp_48.z, fma(temp_80, temp_46, temp_47), temp_86 * max(0.0, fma(temp_65, Env.data[31].z, fma(temp_38, Env.data[27].z, fma(temp_37, Env.data[27].y, temp_36 * Env.data[27].x)) + Env.data[27].w + fma(temp_64, Env.data[30].w, fma(temp_57, Env.data[30].z, fma(temp_59, Env.data[30].y, temp_58 * Env.data[30].x)))))));
    temp_94 = fma(temp_85, temp_87, fma(temp_48.y, fma(temp_75, temp_46, temp_47), temp_85 * max(0.0, fma(temp_65, Env.data[31].y, fma(temp_38, Env.data[26].z, fma(temp_37, Env.data[26].y, temp_36 * Env.data[26].x)) + Env.data[26].w + fma(temp_64, Env.data[29].w, fma(temp_57, Env.data[29].z, fma(temp_59, Env.data[29].y, temp_58 * Env.data[29].x)))))));
    temp_95 = clamp((0.0 - temp_91) + 1.0, 0.0, 1.0);
    temp_96 = clamp((0.0 - fma(temp_91, BlitzUBO0.data[37].w, clamp(fma(temp_49.y, (0.0 - BlitzUBO0.data[36].y), BlitzUBO0.data[36].y) + BlitzUBO0.data[36].x, 0.0, 1.0) + fma(max((0.0 - temp_7.x) + 1.0, (0.0 - temp_7.y) + 1.0), clamp(in_attr3.w + BlitzUBO0.data[36].z, 0.0, 1.0), fma(texture(cGSysProjection0, vec2(in_attr6.x * gl_FragCoord.w * temp_0, in_attr6.y * gl_FragCoord.w * temp_0)).x, (0.0 - Context.data[41].x), Context.data[41].x)))) + 1.0, 0.0, 1.0);
    temp_97 = temp_93;
    temp_98 = temp_90;
    temp_99 = temp_94;
    temp_100 = temp_94;
    temp_101 = temp_90;
    temp_102 = temp_93;
    if (floatBitsToInt(temp_79) != -1)
    {
        temp_103 = floatBitsToInt(temp_79);
        temp_104 = 0;
        do
        {
            temp_105 = temp_103;
            temp_106 = temp_97;
            temp_107 = temp_98;
            temp_108 = temp_99;
            temp_109 = temp_105 & 255;
            temp_100 = temp_108;
            temp_101 = temp_107;
            temp_102 = temp_106;
            temp_110 = uint(temp_109) >= 30u;
            if (temp_110)
            {
                break;
            }
            temp_111 = temp_109 << 4;
            temp_112 = uint(temp_111 + 0x1CC0) >> 2;
            temp_113 = int(temp_112) + 1;
            temp_114 = uint(temp_111 + 0x1CC8) >> 2;
            temp_115 = (0.0 - temp_53) + BlitzUBO2.data[int(temp_112 >> 2)][int(temp_112) & 3];
            temp_116 = BlitzUBO2.data[int(uint(temp_113) >> 2)][temp_113 & 3] + (0.0 - in_attr3.y);
            temp_117 = (0.0 - temp_55) + BlitzUBO2.data[int(temp_114 >> 2)][int(temp_114) & 3];
            temp_118 = fma(temp_117, temp_117, fma(temp_116, temp_116, temp_115 * temp_115));
            temp_119 = temp_115 * inversesqrt(temp_118);
            temp_120 = temp_116 * inversesqrt(temp_118);
            temp_121 = temp_117 * inversesqrt(temp_118);
            temp_122 = temp_32 + temp_119;
            temp_123 = temp_34 + temp_120;
            temp_124 = temp_35 + temp_121;
            temp_125 = uint(temp_111 + 0x1AE0) >> 2;
            temp_126 = int(temp_125) + 1;
            temp_127 = inversesqrt(fma(temp_124, temp_124, fma(temp_123, temp_123, temp_122 * temp_122)));
            temp_128 = temp_122 * temp_127;
            temp_129 = temp_123 * temp_127;
            temp_130 = temp_124 * temp_127;
            temp_131 = max(fma(temp_35, temp_130, fma(temp_34, temp_129, temp_32 * temp_128)), 1E-08);
            temp_132 = fma(temp_38, temp_121, fma(temp_37, temp_120, temp_36 * temp_119));
            temp_133 = max(fma(temp_38, temp_130, fma(temp_37, temp_129, temp_36 * temp_128)), 1E-08) * max(fma(temp_38, temp_130, fma(temp_37, temp_129, temp_36 * temp_128)), 1E-08);
            temp_134 = uint(temp_111 + 0x2080) >> 2;
            temp_135 = max(temp_132, 1E-08);
            temp_136 = uint(temp_111 + 0x1908) >> 2;
            temp_137 = BlitzUBO2.data[int(uint(temp_126) >> 2)][temp_126 & 3] * log2(clamp(fma(BlitzUBO2.data[int(temp_125 >> 2)][int(temp_125) & 3], (0.0 - sqrt(temp_118)), 1.0), 0.0, 1.0));
            temp_138 = uint(temp_111 + 0x1900) >> 2;
            temp_139 = int(temp_138) + 1;
            temp_140 = exp2(temp_131 * fma(temp_131, -5.55473, -6.98316002));
            temp_141 = temp_73 * (1.0 / (temp_70 + fma(temp_70, (0.0 - temp_135), temp_135))) * temp_66 * (1.0 / max(fma(temp_66 * temp_66, temp_133, (0.0 - temp_133)) + 1.0, 1E-08)) * temp_66 * (1.0 / max(fma(temp_66 * temp_66, temp_133, (0.0 - temp_133)) + 1.0, 1E-08));
            temp_142 = floatBitsToInt(BlitzUBO2.data[int(temp_134 >> 2)][int(temp_134) & 3]) != 0;
            temp_143 = temp_137;
            if (!temp_142)
            {
                temp_143 = 1.0;
            }
            temp_144 = temp_143;
            if (temp_142)
            {
                temp_145 = uint(temp_111 + 0x1EA0) >> 2;
                temp_146 = int(temp_145) + 1;
                temp_147 = uint(temp_111 + 0x1EA8) >> 2;
                temp_148 = uint(temp_111 + 0x1AE8) >> 2;
                temp_149 = BlitzUBO2.data[int(temp_148 >> 2)][int(temp_148) & 3];
                temp_150 = int(temp_148) + 1;
                temp_144 = exp2(BlitzUBO2.data[int(uint(temp_150) >> 2)][temp_150 & 3] * log2(clamp(((0.0 - temp_149) + fma(temp_121, (0.0 - BlitzUBO2.data[int(temp_147 >> 2)][int(temp_147) & 3]), fma(temp_120, (0.0 - BlitzUBO2.data[int(uint(temp_146) >> 2)][temp_146 & 3]), temp_119 * (0.0 - BlitzUBO2.data[int(temp_145 >> 2)][int(temp_145) & 3])))) * (1.0 / ((0.0 - temp_149) + 1.0)), 0.0, 1.0)));
            }
            temp_151 = temp_104 + 1;
            temp_152 = exp2(temp_137) * temp_144 * clamp(temp_132 + -0.0, 0.0, 1.0);
            temp_153 = fma(BlitzUBO2.data[int(temp_136 >> 2)][int(temp_136) & 3] * temp_152, fma(temp_84, 0.31830987, (temp_80 + fma(temp_80, (0.0 - temp_140), temp_140)) * temp_141 * 0.0795774683), temp_106);
            temp_154 = fma(BlitzUBO2.data[int(temp_138 >> 2)][int(temp_138) & 3] * temp_152, fma(temp_81, 0.31830987, (temp_77 + fma(temp_77, (0.0 - temp_140), temp_140)) * temp_141 * 0.0795774683), temp_107);
            temp_155 = fma(BlitzUBO2.data[int(uint(temp_139) >> 2)][temp_139 & 3] * temp_152, fma(temp_76, 0.31830987, (temp_75 + fma(temp_75, (0.0 - temp_140), temp_140)) * temp_141 * 0.0795774683), temp_108);
            temp_103 = int(uint(temp_105) >> 8);
            temp_104 = temp_151;
            temp_97 = temp_153;
            temp_98 = temp_154;
            temp_99 = temp_155;
            temp_100 = temp_155;
            temp_101 = temp_154;
            temp_102 = temp_153;
        }
        while (!(temp_151 >= 4));
    }
    temp_110 = false;
    temp_156 = temp_53 + (0.0 - Context.data[11].w);
    temp_157 = in_attr3.y;
    temp_158 = temp_55 + (0.0 - Context.data[13].w);
    temp_159 = fma(temp_95, temp_100, temp_96 * fma(temp_83 * (temp_75 + fma(temp_75, (0.0 - temp_74), temp_74)), 0.07957747, temp_76 * 0.318309873) * fma(temp_92, Env.data[5].y, temp_87));
    temp_160 = temp_157 + (0.0 - Context.data[12].w);
    temp_161 = fma(temp_158, temp_158, fma(temp_160, temp_160, temp_156 * temp_156));
    temp_162 = clamp(fma(fma(temp_55, Env.data[14].z, fma(temp_157, Env.data[14].y, temp_53 * Env.data[14].x)), (0.0 - Env.data[15].x), Env.data[14].w), 0.0, 1.0) * Env.data[13].w;
    temp_163 = fma(temp_95, temp_101, temp_96 * fma(temp_83 * (temp_77 + fma(temp_77, (0.0 - temp_74), temp_74)), 0.07957747, temp_81 * 0.318309873) * fma(temp_92, Env.data[5].x, temp_88));
    temp_164 = clamp(fma(temp_96 * temp_95, BlitzUBO0.data[54].w, 1.0 + (0.0 - BlitzUBO0.data[54].w)), 0.0, 1.0);
    temp_165 = fma(temp_95, temp_102, temp_96 * fma(temp_83 * (temp_80 + fma(temp_80, (0.0 - temp_74), temp_74)), 0.07957747, temp_84 * 0.318309873) * fma(temp_92, Env.data[5].z, temp_89));
    temp_166 = exp2(log2(clamp(sqrt(temp_161) * Context.data[15].x, 0.0, 1.0)) * BlitzUBO0.data[54].x) * exp2(fma(fma(temp_158 * inversesqrt(temp_161), Env.data[23].z, fma(temp_160 * inversesqrt(temp_161), Env.data[23].y, temp_156 * inversesqrt(temp_161) * Env.data[23].x)), (0.0 - BlitzUBO0.data[54].y), BlitzUBO0.data[54].y));
    temp_167 = fma((0.0 - temp_163) + Env.data[13].x, temp_162, temp_163);
    temp_168 = clamp((0.0 - exp2(clamp(fma(sqrt(temp_161), Env.data[12].x, Env.data[11].w), 0.0, 1.0) * (0.0 - BlitzUBO0.data[53].x) * 1.44269502)) + 1.0, 0.0, 1.0) * Env.data[10].w;
    temp_169 = fma((0.0 - temp_165) + Env.data[13].z, temp_162, temp_165);
    temp_170 = fma((0.0 - temp_159) + Env.data[13].y, temp_162, temp_159);
    output_color[0].x = fma((0.0 - temp_167) + fma(fma(temp_166 * BlitzUBO0.data[55].x * temp_164, BlitzUBO0.data[54].z, (0.0 - Env.data[10].x)), BlitzUBO0.data[53].w, Env.data[10].x), temp_168, temp_167);
    output_color[0].y = fma((0.0 - temp_170) + fma(fma(temp_166 * BlitzUBO0.data[55].y * temp_164, BlitzUBO0.data[54].z, (0.0 - Env.data[10].y)), BlitzUBO0.data[53].w, Env.data[10].y), temp_168, temp_170);
    output_color[0].z = fma((0.0 - temp_169) + fma(fma(temp_166 * BlitzUBO0.data[55].z * temp_164, BlitzUBO0.data[54].z, (0.0 - Env.data[10].z)), BlitzUBO0.data[53].w, Env.data[10].z), temp_168, temp_169);
    output_color[0].w = 1.0;
    return;
}
