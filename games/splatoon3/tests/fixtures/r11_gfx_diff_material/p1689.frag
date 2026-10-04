// Hoian_UBER.Product.bfsha model hoian_uber program 1689 (frag)
// sampler cEnvBRDFMap -> loc 24 -> material sampler ?
// sampler cGSysProjection0 -> loc 16 -> material sampler gsys_projection0
// sampler cGSysShadowPrePass -> loc 17 -> material sampler gsys_shadow_prepass
// sampler cPrefilEnvMapArray -> loc 23 -> material sampler ?
// sampler cTexAlbedo -> loc 1 -> material sampler _a0
// sampler cTexBakeAOShadow -> loc 10 -> material sampler _b0
// sampler cTexBakeLight -> loc 11 -> material sampler _b1
// sampler cTexMetalness -> loc 5 -> material sampler _m0
// sampler cTexNormal -> loc 3 -> material sampler _n0
// sampler cTexRoughness -> loc 4 -> material sampler _r0
// ubo BlitzUBO0 -> loc 4 (labelled)
// ubo BlitzUBO2 -> loc 6 (labelled)
// ubo Context -> loc 0 (labelled)
// ubo Env -> loc 2 (labelled)
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

layout (binding = 7, std140) uniform _BlitzUBO0
{
    precise vec4 data[4096];
} BlitzUBO0;

layout (binding = 0) uniform sampler2D cTexNormal;
layout (binding = 1) uniform sampler2D cTexRoughness;
layout (binding = 2) uniform sampler2D cGSysShadowPrePass;
layout (binding = 3) uniform sampler2D cGSysProjection0;
layout (binding = 4) uniform sampler2D cTexAlbedo;
layout (binding = 5) uniform sampler2D cTexMetalness;
layout (binding = 6) uniform sampler2D cEnvBRDFMap;
layout (binding = 7) uniform samplerCubeArray cPrefilEnvMapArray;
layout (binding = 8) uniform sampler2D cTexBakeAOShadow;
layout (binding = 9) uniform sampler2D cTexBakeLight;
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
    precise vec2 temp_2;
    precise float temp_3;
    precise float temp_4;
    precise float temp_5;
    precise float temp_6;
    precise float temp_7;
    precise float temp_8;
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
    precise vec2 temp_40;
    precise vec3 temp_41;
    precise float temp_42;
    precise float temp_43;
    precise float temp_44;
    precise float temp_45;
    precise vec2 temp_46;
    precise float temp_47;
    precise float temp_48;
    precise vec3 temp_49;
    precise vec2 temp_50;
    precise vec4 temp_51;
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
    precise float temp_78;
    precise float temp_79;
    precise float temp_80;
    precise float temp_81;
    uint temp_82;
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
    int temp_98;
    precise float temp_99;
    precise float temp_100;
    precise float temp_101;
    precise float temp_102;
    precise float temp_103;
    precise float temp_104;
    int temp_105;
    int temp_106;
    precise float temp_107;
    precise float temp_108;
    precise float temp_109;
    int temp_110;
    bool temp_111;
    int temp_112;
    uint temp_113;
    int temp_114;
    uint temp_115;
    precise float temp_116;
    precise float temp_117;
    precise float temp_118;
    precise float temp_119;
    precise float temp_120;
    precise float temp_121;
    precise float temp_122;
    precise float temp_123;
    precise float temp_124;
    precise float temp_125;
    uint temp_126;
    int temp_127;
    precise float temp_128;
    precise float temp_129;
    precise float temp_130;
    precise float temp_131;
    precise float temp_132;
    precise float temp_133;
    precise float temp_134;
    uint temp_135;
    precise float temp_136;
    uint temp_137;
    uint temp_138;
    int temp_139;
    precise float temp_140;
    precise float temp_141;
    bool temp_142;
    precise float temp_143;
    precise float temp_144;
    precise float temp_145;
    uint temp_146;
    int temp_147;
    uint temp_148;
    uint temp_149;
    precise float temp_150;
    int temp_151;
    int temp_152;
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
    precise float temp_171;
    temp_111 = false;
    temp_0 = in_attr0.x;
    temp_1 = in_attr0.y;
    temp_2 = texture(cTexNormal, vec2(temp_0, temp_1)).xy;
    temp_3 = temp_2.x;
    temp_4 = temp_2.y;
    temp_5 = in_attr1.x;
    temp_6 = in_attr1.y;
    temp_7 = in_attr1.z;
    temp_8 = in_attr2.y;
    temp_9 = in_attr2.z;
    temp_10 = in_attr2.x;
    temp_11 = in_attr2.w;
    temp_12 = in_attr4.x;
    temp_13 = in_attr4.y;
    temp_14 = in_attr4.z;
    temp_15 = inversesqrt(fma(temp_7, temp_7, fma(temp_6, temp_6, temp_5 * temp_5)));
    temp_16 = temp_7 * temp_15;
    temp_17 = temp_5 * temp_15;
    temp_18 = temp_6 * temp_15;
    temp_19 = sqrt(clamp((0.0 - fma(temp_3, temp_3, temp_4 * temp_4)) + 1.0, 0.0, 1.0));
    temp_20 = fma(temp_17, temp_19, fma(temp_3, temp_10, temp_4 * fma(temp_18, temp_9, (0.0 - temp_16 * temp_8)) * temp_11));
    temp_21 = fma(temp_18, temp_19, fma(temp_3, temp_8, temp_4 * fma(temp_16, temp_10, (0.0 - temp_17 * temp_9)) * temp_11));
    temp_22 = fma(temp_16, temp_19, fma(temp_3, temp_9, temp_4 * fma(temp_17, temp_8, (0.0 - temp_18 * temp_10)) * temp_11));
    temp_23 = inversesqrt(fma(temp_14, temp_14, fma(temp_13, temp_13, temp_12 * temp_12)));
    temp_24 = temp_12 * (0.0 - temp_23);
    temp_25 = inversesqrt(fma(temp_22, temp_22, fma(temp_21, temp_21, temp_20 * temp_20)));
    temp_26 = temp_13 * (0.0 - temp_23);
    temp_27 = temp_14 * (0.0 - temp_23);
    temp_28 = temp_20 * temp_25;
    temp_29 = temp_21 * temp_25;
    temp_30 = 1.0 / (in_attr6.z * gl_FragCoord.w);
    temp_31 = temp_22 * temp_25;
    temp_32 = fma(temp_31, temp_27, fma(temp_29, temp_26, temp_28 * temp_24));
    temp_33 = max(texture(cTexRoughness, vec2(temp_0, temp_1)).x, 0.0001);
    temp_34 = max(temp_32, 1E-08);
    temp_35 = fma(temp_28 * (0.0 - temp_32), -2.0, (0.0 - temp_24));
    temp_36 = fma(temp_29 * (0.0 - temp_32), -2.0, (0.0 - temp_26));
    temp_37 = fma(temp_31 * (0.0 - temp_32), -2.0, (0.0 - temp_27));
    temp_38 = 1.0 / in_attr5.w;
    temp_39 = 1.0 / max(abs(temp_37), max(abs(temp_35), abs(temp_36)));
    temp_40 = texture(cGSysShadowPrePass, vec2(fma(in_attr5.x * temp_38, 0.5, 0.5), fma(in_attr5.y * temp_38, -0.5, 0.5))).xy;
    temp_41 = texture(cTexAlbedo, vec2(temp_0, temp_1)).xyz;
    temp_42 = temp_41.x;
    temp_43 = temp_41.y;
    temp_44 = temp_41.z;
    temp_45 = texture(cTexMetalness, vec2(temp_0, temp_1)).x;
    temp_46 = texture(cEnvBRDFMap, vec2(temp_34, (0.0 - temp_33) + -0.0)).xy;
    temp_47 = temp_46.x;
    temp_48 = temp_46.y;
    temp_49 = texture(cPrefilEnvMapArray, vec4(temp_35 * temp_39, temp_36 * temp_39, temp_37 * temp_39, float(int(clamp(uint(max(roundEven(roundEven(fma(cos(temp_33 * 3.14159274), -5.5, 5.5))), 0.0)), 0u, 0xFFFFu))))).xyz;
    temp_50 = texture(cTexBakeAOShadow, vec2(in_attr7.x, in_attr7.y)).xy;
    temp_51 = texture(cTexBakeLight, vec2(in_attr7.z, in_attr7.w)).xyzw;
    temp_52 = temp_51.w;
    temp_53 = temp_24 + (0.0 - Env.data[23].x);
    temp_54 = temp_26 + (0.0 - Env.data[23].y);
    temp_55 = temp_27 + (0.0 - Env.data[23].z);
    temp_56 = temp_28 * temp_29;
    temp_57 = temp_29 * temp_31;
    temp_58 = inversesqrt(fma(temp_55, temp_55, fma(temp_54, temp_54, temp_53 * temp_53)));
    temp_59 = temp_31 * temp_31;
    temp_60 = in_attr3.x;
    temp_61 = temp_53 * temp_58;
    temp_62 = temp_28 * temp_31;
    temp_63 = in_attr3.z;
    temp_64 = temp_54 * temp_58;
    temp_65 = temp_55 * temp_58;
    temp_66 = fma(temp_28, temp_28, (0.0 - temp_29 * temp_29));
    temp_67 = temp_33 * temp_33;
    temp_68 = fma(temp_33, 0.5, 0.5);
    temp_69 = fma(temp_29, (0.0 - Env.data[23].y), temp_28 * (0.0 - Env.data[23].x));
    temp_70 = max(fma(temp_31, temp_65, fma(temp_29, temp_64, temp_28 * temp_61)), 1E-08) * max(fma(temp_31, temp_65, fma(temp_29, temp_64, temp_28 * temp_61)), 1E-08);
    temp_71 = temp_68 * 0.5 * temp_68;
    temp_72 = max(fma(temp_31, (0.0 - Env.data[23].z), temp_69), 1E-08);
    temp_73 = 1.0 / (temp_71 + fma(temp_34, (0.0 - temp_71), temp_34));
    temp_74 = max(fma(temp_27, temp_65, fma(temp_26, temp_64, temp_24 * temp_61)), 1E-08);
    temp_75 = fma(temp_43, (0.0 - temp_45), temp_43);
    temp_76 = temp_73 * (1.0 / (temp_71 + fma(temp_71, (0.0 - temp_72), temp_72))) * temp_67 * (1.0 / max(fma(temp_70, temp_67 * temp_67, (0.0 - temp_70)) + 1.0, 1E-08)) * temp_67 * (1.0 / max(fma(temp_70, temp_67 * temp_67, (0.0 - temp_70)) + 1.0, 1E-08));
    temp_77 = fma(temp_42, (0.0 - temp_45), temp_42);
    temp_78 = fma(temp_45, temp_44 + -0.0399999991, 0.04);
    temp_79 = exp2(temp_74 * fma(temp_74, -5.55473, -6.98316002));
    temp_80 = fma(temp_45, temp_42 + -0.0399999991, 0.04);
    temp_81 = fma(temp_45, temp_43 + -0.0399999991, 0.04);
    temp_82 = uint(max(0, min(int(trunc((temp_63 + (0.0 - BlitzUBO2.data[0x226].z)) * BlitzUBO2.data[0x227].z)), 19)) * 20 + max(0, min(int(trunc((temp_60 + (0.0 - BlitzUBO2.data[0x226].x)) * BlitzUBO2.data[0x227].x)), 19)) << 4) >> 2;
    temp_83 = BlitzUBO2.data[int(temp_82 >> 2)][int(temp_82) & 3];
    temp_84 = fma(temp_80, (0.0 - temp_77), temp_77);
    temp_85 = fma(temp_44, (0.0 - temp_45), temp_44);
    temp_86 = fma(temp_81, (0.0 - temp_75), temp_75);
    temp_87 = fma(temp_78, (0.0 - temp_85), temp_85);
    temp_88 = clamp(fma(temp_50.x, (0.0 - BlitzUBO0.data[37].x), BlitzUBO0.data[37].x) + BlitzUBO0.data[37].y, 0.0, 1.0);
    temp_89 = temp_51.x * temp_52 * 32.0;
    temp_90 = temp_51.y * temp_52 * 32.0;
    temp_91 = temp_51.z * temp_52 * 32.0;
    temp_92 = fma(temp_84, temp_89, fma(temp_49.x, fma(temp_80, temp_47, temp_48), temp_84 * max(0.0, fma(temp_66, Env.data[31].x, fma(temp_31, Env.data[25].z, fma(temp_29, Env.data[25].y, temp_28 * Env.data[25].x)) + Env.data[25].w + fma(temp_62, Env.data[28].w, fma(temp_59, Env.data[28].z, fma(temp_57, Env.data[28].y, temp_56 * Env.data[28].x)))))));
    temp_93 = clamp(fma(temp_31, (0.0 - Env.data[23].z), temp_69), 0.0, 1.0);
    temp_94 = fma(temp_86, temp_90, fma(temp_49.y, fma(temp_81, temp_47, temp_48), temp_86 * max(0.0, fma(temp_66, Env.data[31].y, fma(temp_31, Env.data[26].z, fma(temp_29, Env.data[26].y, temp_28 * Env.data[26].x)) + Env.data[26].w + fma(temp_62, Env.data[29].w, fma(temp_59, Env.data[29].z, fma(temp_57, Env.data[29].y, temp_56 * Env.data[29].x)))))));
    temp_95 = fma(temp_87, temp_91, fma(temp_49.z, fma(temp_78, temp_47, temp_48), temp_87 * max(0.0, fma(temp_66, Env.data[31].z, fma(temp_31, Env.data[27].z, fma(temp_29, Env.data[27].y, temp_28 * Env.data[27].x)) + Env.data[27].w + fma(temp_62, Env.data[30].w, fma(temp_59, Env.data[30].z, fma(temp_57, Env.data[30].y, temp_56 * Env.data[30].x)))))));
    temp_96 = clamp((0.0 - temp_88) + 1.0, 0.0, 1.0);
    temp_97 = clamp((0.0 - fma(temp_88, BlitzUBO0.data[37].w, clamp(fma(temp_50.y, (0.0 - BlitzUBO0.data[36].y), BlitzUBO0.data[36].y) + BlitzUBO0.data[36].x, 0.0, 1.0) + fma(max((0.0 - temp_40.x) + 1.0, (0.0 - temp_40.y) + 1.0), clamp(in_attr3.w + BlitzUBO0.data[36].z, 0.0, 1.0), fma(texture(cGSysProjection0, vec2(in_attr6.x * gl_FragCoord.w * temp_30, in_attr6.y * gl_FragCoord.w * temp_30)).x, (0.0 - Context.data[41].x), Context.data[41].x)))) + 1.0, 0.0, 1.0);
    temp_98 = floatBitsToInt(temp_83);
    temp_99 = temp_94;
    temp_100 = temp_95;
    temp_101 = temp_92;
    temp_102 = temp_92;
    temp_103 = temp_94;
    temp_104 = temp_95;
    if (floatBitsToInt(temp_83) != -1)
    {
        temp_105 = 0;
        do
        {
            temp_106 = temp_98;
            temp_107 = temp_99;
            temp_108 = temp_100;
            temp_109 = temp_101;
            temp_110 = temp_106 & 255;
            temp_102 = temp_109;
            temp_103 = temp_107;
            temp_104 = temp_108;
            temp_111 = uint(temp_110) >= 30u;
            if (temp_111)
            {
                break;
            }
            temp_112 = temp_110 << 4;
            temp_113 = uint(temp_112 + 0x1CC0) >> 2;
            temp_114 = int(temp_113) + 1;
            temp_115 = uint(temp_112 + 0x1CC8) >> 2;
            temp_116 = (0.0 - temp_60) + BlitzUBO2.data[int(temp_113 >> 2)][int(temp_113) & 3];
            temp_117 = BlitzUBO2.data[int(uint(temp_114) >> 2)][temp_114 & 3] + (0.0 - in_attr3.y);
            temp_118 = (0.0 - temp_63) + BlitzUBO2.data[int(temp_115 >> 2)][int(temp_115) & 3];
            temp_119 = fma(temp_118, temp_118, fma(temp_117, temp_117, temp_116 * temp_116));
            temp_120 = temp_116 * inversesqrt(temp_119);
            temp_121 = temp_117 * inversesqrt(temp_119);
            temp_122 = temp_118 * inversesqrt(temp_119);
            temp_123 = temp_24 + temp_120;
            temp_124 = temp_26 + temp_121;
            temp_125 = temp_27 + temp_122;
            temp_126 = uint(temp_112 + 0x1AE0) >> 2;
            temp_127 = int(temp_126) + 1;
            temp_128 = inversesqrt(fma(temp_125, temp_125, fma(temp_124, temp_124, temp_123 * temp_123)));
            temp_129 = temp_123 * temp_128;
            temp_130 = temp_124 * temp_128;
            temp_131 = temp_125 * temp_128;
            temp_132 = max(fma(temp_27, temp_131, fma(temp_26, temp_130, temp_24 * temp_129)), 1E-08);
            temp_133 = fma(temp_31, temp_122, fma(temp_29, temp_121, temp_28 * temp_120));
            temp_134 = max(fma(temp_31, temp_131, fma(temp_29, temp_130, temp_28 * temp_129)), 1E-08) * max(fma(temp_31, temp_131, fma(temp_29, temp_130, temp_28 * temp_129)), 1E-08);
            temp_135 = uint(temp_112 + 0x2080) >> 2;
            temp_136 = max(temp_133, 1E-08);
            temp_137 = uint(temp_112 + 0x1908) >> 2;
            temp_138 = uint(temp_112 + 0x1900) >> 2;
            temp_139 = int(temp_138) + 1;
            temp_140 = exp2(temp_132 * fma(temp_132, -5.55473, -6.98316002));
            temp_141 = temp_73 * (1.0 / (temp_71 + fma(temp_71, (0.0 - temp_136), temp_136))) * temp_67 * (1.0 / max(fma(temp_67 * temp_67, temp_134, (0.0 - temp_134)) + 1.0, 1E-08)) * temp_67 * (1.0 / max(fma(temp_67 * temp_67, temp_134, (0.0 - temp_134)) + 1.0, 1E-08));
            temp_142 = floatBitsToInt(BlitzUBO2.data[int(temp_135 >> 2)][int(temp_135) & 3]) != 0;
            temp_143 = temp_80 + fma(temp_80, (0.0 - temp_140), temp_140);
            temp_144 = temp_143;
            if (!temp_142)
            {
                temp_144 = 1.0;
            }
            temp_145 = temp_144;
            if (temp_142)
            {
                temp_146 = uint(temp_112 + 0x1EA0) >> 2;
                temp_147 = int(temp_146) + 1;
                temp_148 = uint(temp_112 + 0x1EA8) >> 2;
                temp_149 = uint(temp_112 + 0x1AE8) >> 2;
                temp_150 = BlitzUBO2.data[int(temp_149 >> 2)][int(temp_149) & 3];
                temp_151 = int(temp_149) + 1;
                temp_145 = exp2(BlitzUBO2.data[int(uint(temp_151) >> 2)][temp_151 & 3] * log2(clamp(((0.0 - temp_150) + fma(temp_122, (0.0 - BlitzUBO2.data[int(temp_148 >> 2)][int(temp_148) & 3]), fma(temp_121, (0.0 - BlitzUBO2.data[int(uint(temp_147) >> 2)][temp_147 & 3]), temp_120 * (0.0 - BlitzUBO2.data[int(temp_146 >> 2)][int(temp_146) & 3])))) * (1.0 / ((0.0 - temp_150) + 1.0)), 0.0, 1.0)));
            }
            temp_152 = temp_105 + 1;
            temp_153 = exp2(BlitzUBO2.data[int(uint(temp_127) >> 2)][temp_127 & 3] * log2(clamp(fma(BlitzUBO2.data[int(temp_126 >> 2)][int(temp_126) & 3], (0.0 - sqrt(temp_119)), 1.0), 0.0, 1.0))) * temp_145 * clamp(temp_133 + -0.0, 0.0, 1.0);
            temp_154 = fma(BlitzUBO2.data[int(uint(temp_139) >> 2)][temp_139 & 3] * temp_153, fma(temp_75, 0.31830987, (temp_81 + fma(temp_81, (0.0 - temp_140), temp_140)) * temp_141 * 0.0795774683), temp_107);
            temp_155 = fma(BlitzUBO2.data[int(temp_137 >> 2)][int(temp_137) & 3] * temp_153, fma(temp_85, 0.31830987, (temp_78 + fma(temp_78, (0.0 - temp_140), temp_140)) * temp_141 * 0.0795774683), temp_108);
            temp_156 = fma(BlitzUBO2.data[int(temp_138 >> 2)][int(temp_138) & 3] * temp_153, fma(temp_77, 0.31830987, temp_143 * temp_141 * 0.0795774683), temp_109);
            temp_98 = int(uint(temp_106) >> 8);
            temp_105 = temp_152;
            temp_99 = temp_154;
            temp_100 = temp_155;
            temp_101 = temp_156;
            temp_102 = temp_156;
            temp_103 = temp_154;
            temp_104 = temp_155;
        }
        while (!(temp_152 >= 4));
    }
    temp_111 = false;
    temp_157 = temp_60 + (0.0 - Context.data[11].w);
    temp_158 = in_attr3.y;
    temp_159 = temp_63 + (0.0 - Context.data[13].w);
    temp_160 = temp_158 + (0.0 - Context.data[12].w);
    temp_161 = fma(temp_159, temp_159, fma(temp_160, temp_160, temp_157 * temp_157));
    temp_162 = fma(temp_96, temp_102, temp_97 * fma(temp_76 * (temp_80 + fma(temp_80, (0.0 - temp_79), temp_79)), 0.07957747, temp_77 * 0.318309873) * fma(temp_93, Env.data[5].x, temp_89));
    temp_163 = clamp(fma(temp_97 * temp_96, BlitzUBO0.data[54].w, 1.0 + (0.0 - BlitzUBO0.data[54].w)), 0.0, 1.0);
    temp_164 = fma(temp_96, temp_103, temp_97 * fma(temp_76 * (temp_81 + fma(temp_81, (0.0 - temp_79), temp_79)), 0.07957747, temp_75 * 0.318309873) * fma(temp_93, Env.data[5].y, temp_90));
    temp_165 = clamp(fma(fma(temp_63, Env.data[14].z, fma(temp_158, Env.data[14].y, temp_60 * Env.data[14].x)), (0.0 - Env.data[15].x), Env.data[14].w), 0.0, 1.0) * Env.data[13].w;
    temp_166 = fma(temp_96, temp_104, temp_97 * fma(temp_76 * (temp_78 + fma(temp_78, (0.0 - temp_79), temp_79)), 0.07957747, temp_85 * 0.318309873) * fma(temp_93, Env.data[5].z, temp_91));
    temp_167 = exp2(log2(clamp(sqrt(temp_161) * Context.data[15].x, 0.0, 1.0)) * BlitzUBO0.data[54].x) * exp2(fma(fma(temp_159 * inversesqrt(temp_161), Env.data[23].z, fma(temp_160 * inversesqrt(temp_161), Env.data[23].y, temp_157 * inversesqrt(temp_161) * Env.data[23].x)), (0.0 - BlitzUBO0.data[54].y), BlitzUBO0.data[54].y));
    temp_168 = fma((0.0 - temp_162) + Env.data[13].x, temp_165, temp_162);
    temp_169 = fma((0.0 - temp_166) + Env.data[13].z, temp_165, temp_166);
    temp_170 = fma((0.0 - temp_164) + Env.data[13].y, temp_165, temp_164);
    temp_171 = clamp((0.0 - exp2(clamp(fma(sqrt(temp_161), Env.data[12].x, Env.data[11].w), 0.0, 1.0) * (0.0 - BlitzUBO0.data[53].x) * 1.44269502)) + 1.0, 0.0, 1.0) * Env.data[10].w;
    output_color[0].x = fma((0.0 - temp_168) + fma(fma(temp_167 * BlitzUBO0.data[55].x * temp_163, BlitzUBO0.data[54].z, (0.0 - Env.data[10].x)), BlitzUBO0.data[53].w, Env.data[10].x), temp_171, temp_168);
    output_color[0].y = fma((0.0 - temp_170) + fma(fma(temp_167 * BlitzUBO0.data[55].y * temp_163, BlitzUBO0.data[54].z, (0.0 - Env.data[10].y)), BlitzUBO0.data[53].w, Env.data[10].y), temp_171, temp_170);
    output_color[0].z = fma((0.0 - temp_169) + fma(fma(temp_167 * BlitzUBO0.data[55].z * temp_163, BlitzUBO0.data[54].z, (0.0 - Env.data[10].z)), BlitzUBO0.data[53].w, Env.data[10].z), temp_171, temp_169);
    output_color[0].w = 1.0;
    return;
}
