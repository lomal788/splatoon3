// Hoian_UBER.Product.bfsha model hoian_uber program 1714 (frag)
// sampler cBlitzWallPaintGrid -> loc 26 -> material sampler gsys_user3
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

layout (binding = 7, std140) uniform _BlitzUBO0
{
    precise vec4 data[4096];
} BlitzUBO0;

layout (binding = 1, std140) uniform _fp_c1
{
    precise vec4 data[4096];
} fp_c1;

layout (binding = 3, std140) uniform _Context
{
    precise vec4 data[4096];
} Context;

layout (binding = 5, std140) uniform _Env
{
    precise vec4 data[4096];
} Env;

layout (binding = 0) uniform sampler2D cBlitzWallPaintGrid;
layout (binding = 1) uniform sampler2D cTexNormal;
layout (binding = 2) uniform sampler2D cTexAlbedo;
layout (binding = 3) uniform sampler2D cTexRoughness;
layout (binding = 4) uniform sampler2D cTexMetalness;
layout (binding = 5) uniform sampler2D cGSysShadowPrePass;
layout (binding = 6) uniform sampler2D cGSysProjection0;
layout (binding = 7) uniform sampler2D cTexBakeAOShadow;
layout (binding = 8) uniform sampler2D cTexBakeLight;
layout (binding = 9) uniform sampler2D cEnvBRDFMap;
layout (binding = 10) uniform samplerCubeArray cPrefilEnvMapArray;
layout (location = 0) in vec4 in_attr0;
layout (location = 1) in vec4 in_attr1;
layout (location = 2) in vec4 in_attr2;
layout (location = 3) in vec4 in_attr3;
layout (location = 4) in vec4 in_attr4;
layout (location = 5) in vec4 in_attr5;
layout (location = 6) in vec4 in_attr6;
layout (location = 7) in vec4 in_attr7;
layout (location = 8) in vec4 in_attr8;
layout (location = 9) in vec4 in_attr9;
layout (location = 10) in vec4 in_attr10;

layout (location = 0) out vec4 output_color[0];


void main()
{
    precise float temp_0;
    bool temp_1;
    precise float temp_2;
    precise float temp_3;
    precise float temp_4;
    precise float temp_5;
    precise float temp_6;
    precise vec3 temp_7;
    precise float temp_8;
    precise float temp_9;
    precise float temp_10;
    precise vec3 temp_11;
    precise vec3 temp_12;
    precise vec2 temp_13;
    precise float temp_14;
    precise float temp_15;
    precise vec3 temp_16;
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
    precise float temp_45;
    precise float temp_46;
    precise float temp_47;
    precise float temp_48;
    precise float temp_49;
    bool temp_50;
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
    precise float temp_78;
    precise float temp_79;
    precise float temp_80;
    precise float temp_81;
    precise float temp_82;
    precise float temp_83;
    precise float temp_84;
    precise float temp_85;
    precise vec2 temp_86;
    precise float temp_87;
    precise float temp_88;
    precise float temp_89;
    precise float temp_90;
    precise float temp_91;
    precise vec2 temp_92;
    precise float temp_93;
    precise float temp_94;
    precise vec4 temp_95;
    precise float temp_96;
    precise vec2 temp_97;
    precise float temp_98;
    precise float temp_99;
    precise float temp_100;
    precise float temp_101;
    precise float temp_102;
    precise float temp_103;
    precise float temp_104;
    precise float temp_105;
    precise float temp_106;
    precise float temp_107;
    precise float temp_108;
    precise float temp_109;
    precise float temp_110;
    precise float temp_111;
    precise float temp_112;
    precise float temp_113;
    precise float temp_114;
    precise float temp_115;
    precise vec3 temp_116;
    precise float temp_117;
    precise float temp_118;
    precise float temp_119;
    precise float temp_120;
    precise float temp_121;
    precise float temp_122;
    precise float temp_123;
    precise float temp_124;
    precise float temp_125;
    precise float temp_126;
    precise float temp_127;
    precise float temp_128;
    precise float temp_129;
    precise float temp_130;
    precise vec2 temp_131;
    precise float temp_132;
    precise float temp_133;
    precise vec3 temp_134;
    precise float temp_135;
    precise float temp_136;
    precise float temp_137;
    precise float temp_138;
    precise float temp_139;
    precise float temp_140;
    precise float temp_141;
    precise float temp_142;
    precise float temp_143;
    precise float temp_144;
    precise float temp_145;
    precise float temp_146;
    precise float temp_147;
    precise float temp_148;
    precise float temp_149;
    precise float temp_150;
    precise float temp_151;
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
    uint temp_162;
    precise float temp_163;
    precise float temp_164;
    precise float temp_165;
    precise float temp_166;
    precise float temp_167;
    precise float temp_168;
    precise float temp_169;
    precise float temp_170;
    precise float temp_171;
    precise float temp_172;
    precise float temp_173;
    precise float temp_174;
    precise float temp_175;
    precise float temp_176;
    precise float temp_177;
    precise float temp_178;
    precise float temp_179;
    precise float temp_180;
    precise float temp_181;
    precise float temp_182;
    precise float temp_183;
    int temp_184;
    int temp_185;
    int temp_186;
    precise float temp_187;
    precise float temp_188;
    precise float temp_189;
    int temp_190;
    bool temp_191;
    int temp_192;
    uint temp_193;
    int temp_194;
    uint temp_195;
    precise float temp_196;
    precise float temp_197;
    precise float temp_198;
    precise float temp_199;
    precise float temp_200;
    precise float temp_201;
    precise float temp_202;
    precise float temp_203;
    precise float temp_204;
    precise float temp_205;
    uint temp_206;
    int temp_207;
    precise float temp_208;
    precise float temp_209;
    precise float temp_210;
    precise float temp_211;
    precise float temp_212;
    precise float temp_213;
    uint temp_214;
    precise float temp_215;
    precise float temp_216;
    uint temp_217;
    uint temp_218;
    int temp_219;
    precise float temp_220;
    bool temp_221;
    precise float temp_222;
    precise float temp_223;
    precise float temp_224;
    precise float temp_225;
    uint temp_226;
    int temp_227;
    uint temp_228;
    precise float temp_229;
    int temp_230;
    uint temp_231;
    int temp_232;
    precise float temp_233;
    precise float temp_234;
    precise float temp_235;
    precise float temp_236;
    precise float temp_237;
    precise float temp_238;
    precise float temp_239;
    precise float temp_240;
    precise float temp_241;
    precise float temp_242;
    precise float temp_243;
    precise float temp_244;
    precise float temp_245;
    precise float temp_246;
    precise float temp_247;
    precise float temp_248;
    precise float temp_249;
    precise float temp_250;
    precise float temp_251;
    precise float temp_252;
    temp_191 = false;
    temp_0 = in_attr0.y;
    temp_1 = in_attr7.w < 0.0;
    temp_2 = in_attr6.y;
    temp_3 = in_attr6.x;
    if (temp_1)
    {
        temp_2 = in_attr6.w;
    }
    if (temp_1)
    {
        temp_3 = in_attr6.z;
    }
    temp_4 = temp_3;
    temp_5 = (0.0 - temp_2) + 1.0;
    temp_6 = in_attr0.x;
    temp_7 = texture(cBlitzWallPaintGrid, vec2(temp_4, temp_5)).xyz;
    temp_8 = temp_7.x;
    temp_9 = temp_7.y;
    temp_10 = temp_7.z;
    temp_11 = texture(cBlitzWallPaintGrid, vec2(temp_4, fma(BlitzUBO0.data[20].z, BlitzUBO0.data[22].w, temp_5))).xyz;
    temp_12 = texture(cBlitzWallPaintGrid, vec2(fma(BlitzUBO0.data[20].z, BlitzUBO0.data[22].z, temp_4), temp_5)).xyz;
    temp_13 = texture(cTexNormal, vec2(temp_6, temp_0)).xy;
    temp_14 = temp_13.x;
    temp_15 = temp_13.y;
    temp_16 = texture(cTexAlbedo, vec2(temp_6, temp_0)).xyz;
    temp_17 = in_attr1.x;
    temp_18 = in_attr1.y;
    temp_19 = in_attr1.z;
    temp_20 = in_attr2.y;
    temp_21 = in_attr2.z;
    temp_22 = in_attr2.x;
    temp_23 = in_attr2.w;
    temp_24 = in_attr9.y;
    temp_25 = in_attr9.x;
    temp_26 = 1.0 / in_attr5.w;
    temp_27 = inversesqrt(fma(temp_19, temp_19, fma(temp_18, temp_18, temp_17 * temp_17)));
    temp_28 = temp_19 * temp_27;
    temp_29 = temp_17 * temp_27;
    temp_30 = temp_18 * temp_27;
    temp_31 = in_attr9.z;
    temp_32 = max(temp_10, max(temp_8, temp_9));
    temp_33 = temp_32 + (0.0 - BlitzUBO0.data[21].w);
    temp_34 = clamp(temp_33 + -0.0, 0.0, 1.0);
    temp_35 = clamp((temp_9 + (0.0 - temp_32) + 9.99999975E-05) * 100000000.0, 0.0, 1.0);
    temp_36 = clamp((temp_8 + (0.0 - temp_32) + 9.99999975E-05) * 100000000.0, 0.0, 1.0);
    temp_37 = clamp((temp_10 + (0.0 - temp_32) + 9.99999975E-05) * 100000000.0, 0.0, 1.0);
    temp_38 = fma(clamp(temp_30 + -0.0, 0.0, 1.0), (0.0 - BlitzUBO0.data[20].y) + BlitzUBO0.data[20].x, BlitzUBO0.data[20].y);
    temp_39 = sqrt(clamp((0.0 - fma(temp_14, temp_14, temp_15 * temp_15)) + 1.0, 0.0, 1.0));
    temp_40 = fma(temp_10 + (0.0 - temp_11.z), temp_37, fma(temp_8 + (0.0 - temp_11.x), temp_36, (temp_9 + (0.0 - temp_11.y)) * temp_35)) * BlitzUBO0.data[18].y;
    temp_41 = fma(temp_10 + (0.0 - temp_12.z), temp_37, fma(temp_8 + (0.0 - temp_12.x), temp_36, (temp_9 + (0.0 - temp_12.y)) * temp_35)) * BlitzUBO0.data[18].y;
    temp_42 = fma(temp_29, temp_39, fma(temp_22, temp_14, temp_15 * fma(temp_30, temp_21, (0.0 - temp_28 * temp_20)) * temp_23));
    temp_43 = temp_29 + fma(temp_25, temp_41, temp_40 * fma(temp_30, temp_31, (0.0 - temp_28 * temp_24)));
    temp_44 = temp_30 + fma(temp_24, temp_41, temp_40 * fma(temp_28, temp_25, (0.0 - temp_29 * temp_31)));
    temp_45 = fma(temp_30, temp_39, fma(temp_20, temp_14, temp_15 * fma(temp_28, temp_22, (0.0 - temp_29 * temp_21)) * temp_23));
    temp_46 = fma(temp_28, temp_39, fma(temp_21, temp_14, temp_15 * fma(temp_29, temp_20, (0.0 - temp_30 * temp_22)) * temp_23));
    temp_47 = temp_28 + fma(temp_31, temp_41, temp_40 * fma(temp_29, temp_24, (0.0 - temp_30 * temp_25)));
    temp_48 = inversesqrt(fma(temp_46, temp_46, fma(temp_45, temp_45, temp_42 * temp_42)));
    temp_49 = inversesqrt(fma(temp_47, temp_47, fma(temp_44, temp_44, temp_43 * temp_43)));
    temp_50 = min(temp_34 * 1000.0, 1.0) > 0.5;
    temp_51 = fma(temp_37, BlitzUBO0.data[63].x, fma(temp_36, BlitzUBO0.data[4].x, temp_35 * BlitzUBO0.data[11].x));
    temp_52 = fma(temp_37, BlitzUBO0.data[63].y, fma(temp_36, BlitzUBO0.data[4].y, temp_35 * BlitzUBO0.data[11].y));
    temp_53 = fma(temp_37, BlitzUBO0.data[63].z, fma(temp_36, BlitzUBO0.data[4].z, temp_35 * BlitzUBO0.data[11].z));
    temp_54 = temp_42 * temp_48;
    temp_55 = temp_45 * temp_48;
    temp_56 = temp_46 * temp_48;
    temp_57 = temp_43 * temp_49;
    temp_58 = temp_47 * temp_49;
    temp_59 = temp_44 * temp_49;
    temp_60 = temp_54;
    temp_61 = temp_55;
    temp_62 = temp_56;
    temp_63 = temp_16.z;
    temp_64 = temp_16.x;
    temp_65 = temp_16.y;
    if (temp_50)
    {
        temp_66 = clamp(temp_34 * BlitzUBO0.data[45].z, 0.0, 1.0);
        temp_67 = fma(fma(temp_53, (0.0 - BlitzUBO0.data[45].y), fma(temp_37, BlitzUBO0.data[62].z, fma(temp_36, BlitzUBO0.data[3].z, temp_35 * BlitzUBO0.data[10].z))), temp_66, temp_53 * BlitzUBO0.data[45].y);
        temp_68 = fma(fma(temp_51, (0.0 - BlitzUBO0.data[45].y), fma(temp_37, BlitzUBO0.data[62].x, fma(temp_36, BlitzUBO0.data[3].x, temp_35 * BlitzUBO0.data[10].x))), temp_66, temp_51 * BlitzUBO0.data[45].y);
        temp_69 = fma(fma(temp_52, (0.0 - BlitzUBO0.data[45].y), fma(temp_37, BlitzUBO0.data[62].y, fma(temp_36, BlitzUBO0.data[3].y, temp_35 * BlitzUBO0.data[10].y))), temp_66, temp_52 * BlitzUBO0.data[45].y);
        temp_70 = BlitzUBO0.data[18].x;
        temp_60 = fma(temp_38, temp_57 + (0.0 - temp_54), temp_54);
        temp_61 = fma(temp_38, temp_59 + (0.0 - temp_55), temp_55);
        temp_62 = fma(temp_38, temp_58 + (0.0 - temp_56), temp_56);
        temp_63 = temp_67;
        temp_71 = 0.0;
        temp_64 = temp_68;
        temp_65 = temp_69;
        temp_72 = temp_68 * BlitzUBO0.data[18].z;
        temp_73 = temp_69 * BlitzUBO0.data[18].z;
        temp_74 = temp_67 * BlitzUBO0.data[18].z;
    }
    else
    {
        temp_70 = max(texture(cTexRoughness, vec2(temp_6, temp_0)).x, 0.0001);
        temp_71 = texture(cTexMetalness, vec2(temp_6, temp_0)).x;
        temp_72 = 0.0;
        temp_73 = 0.0;
        temp_74 = 0.0;
    }
    temp_75 = temp_70;
    temp_76 = temp_60;
    temp_77 = temp_61;
    temp_78 = temp_62;
    temp_79 = temp_63;
    temp_80 = temp_71;
    temp_81 = temp_64;
    temp_82 = temp_65;
    temp_83 = in_attr4.x;
    temp_84 = in_attr4.y;
    temp_85 = in_attr4.z;
    temp_86 = texture(cGSysShadowPrePass, vec2(fma(in_attr5.x * temp_26, 0.5, 0.5), fma(in_attr5.y * temp_26, -0.5, 0.5))).xy;
    temp_87 = 1.0 / (in_attr8.z * gl_FragCoord.w);
    temp_88 = inversesqrt(fma(temp_85, temp_85, fma(temp_84, temp_84, temp_83 * temp_83)));
    temp_89 = temp_83 * (0.0 - temp_88);
    temp_90 = temp_84 * (0.0 - temp_88);
    temp_91 = temp_85 * (0.0 - temp_88);
    temp_92 = texture(cTexBakeAOShadow, vec2(in_attr10.x, in_attr10.y)).xy;
    temp_93 = fma(temp_91, temp_78, fma(temp_90, temp_77, temp_89 * temp_76));
    temp_94 = max(temp_93, 1E-08);
    temp_95 = texture(cTexBakeLight, vec2(in_attr10.z, in_attr10.w)).xyzw;
    temp_96 = temp_95.w;
    temp_97 = texture(cEnvBRDFMap, vec2(temp_94, (0.0 - temp_75) + -0.0)).xy;
    temp_98 = fma(temp_81, (0.0 - temp_80), temp_81);
    temp_99 = fma(temp_82, (0.0 - temp_80), temp_82);
    temp_100 = clamp(fma(temp_92.x, (0.0 - BlitzUBO0.data[37].x), BlitzUBO0.data[37].x) + BlitzUBO0.data[37].y, 0.0, 1.0);
    temp_101 = fma(temp_81 + -0.0399999991, temp_80, 0.04);
    temp_102 = fma(temp_82 + -0.0399999991, temp_80, 0.04);
    temp_103 = fma(temp_79 + -0.0399999991, temp_80, 0.04);
    temp_104 = fma(temp_79, (0.0 - temp_80), temp_79);
    temp_105 = clamp((0.0 - temp_100) + 1.0, 0.0, 1.0);
    temp_106 = clamp((0.0 - fma(temp_100, BlitzUBO0.data[37].w, fma(max((0.0 - temp_86.x) + 1.0, (0.0 - temp_86.y) + 1.0), clamp(in_attr3.w + BlitzUBO0.data[36].z, 0.0, 1.0), fma(texture(cGSysProjection0, vec2(in_attr8.x * gl_FragCoord.w * temp_87, in_attr8.y * gl_FragCoord.w * temp_87)).x, (0.0 - Context.data[41].x), Context.data[41].x)) + clamp(fma(temp_92.y, (0.0 - BlitzUBO0.data[36].y), BlitzUBO0.data[36].y) + BlitzUBO0.data[36].x, 0.0, 1.0))) + 1.0, 0.0, 1.0);
    temp_107 = temp_94;
    temp_108 = temp_101;
    temp_109 = temp_102;
    temp_110 = temp_103;
    if (temp_50)
    {
        temp_111 = fma(temp_91, (0.0 - temp_78), fma(temp_90, (0.0 - temp_77), temp_89 * (0.0 - temp_76)));
        temp_112 = fma(temp_111 * temp_76, -2.0, (0.0 - temp_89));
        temp_113 = fma(temp_111 * temp_77, -2.0, (0.0 - temp_90));
        temp_114 = fma(temp_111 * temp_78, -2.0, (0.0 - temp_91));
        temp_115 = 1.0 / max(abs(temp_114), max(abs(temp_112), abs(temp_113)));
        temp_116 = texture(cPrefilEnvMapArray, vec4(temp_112 * temp_115, temp_113 * temp_115, temp_114 * temp_115, float(12)), 0.0).xyz;
        temp_117 = fma(temp_97.x, BlitzUBO0.data[19].x, temp_97.y);
        temp_118 = fma(temp_77 + -1.0, BlitzUBO0.data[19].z, 1.0);
        temp_119 = temp_76 * BlitzUBO0.data[19].z;
        temp_120 = temp_78 * BlitzUBO0.data[19].z;
        temp_108 = BlitzUBO0.data[19].x;
        temp_109 = BlitzUBO0.data[19].x;
        temp_110 = BlitzUBO0.data[19].x;
        temp_121 = temp_116.x * temp_117;
        temp_122 = temp_116.z * temp_117;
        temp_123 = temp_116.y * temp_117;
        temp_124 = 1.0;
    }
    else
    {
        temp_125 = max(temp_93, 1E-08);
        temp_126 = fma(temp_91, (0.0 - temp_78), fma(temp_90, (0.0 - temp_77), temp_89 * (0.0 - temp_76)));
        temp_127 = fma(temp_126 * temp_76, -2.0, (0.0 - temp_89));
        temp_128 = fma(temp_126 * temp_77, -2.0, (0.0 - temp_90));
        temp_129 = fma(temp_126 * temp_78, -2.0, (0.0 - temp_91));
        temp_130 = 1.0 / max(abs(temp_129), max(abs(temp_127), abs(temp_128)));
        temp_131 = texture(cEnvBRDFMap, vec2(temp_125, (0.0 - temp_75) + -0.0)).xy;
        temp_132 = temp_131.x;
        temp_133 = temp_131.y;
        temp_134 = texture(cPrefilEnvMapArray, vec4(temp_127 * temp_130, temp_128 * temp_130, temp_129 * temp_130, float(int(clamp(uint(max(roundEven(roundEven(fma(cos(temp_75 * 3.14159274), -5.5, 5.5))), 0.0)), 0u, 0xFFFFu))))).xyz;
        temp_135 = fma(fma(temp_58, (0.0 - Env.data[23].z), fma(temp_59, (0.0 - Env.data[23].y), temp_57 * (0.0 - Env.data[23].x))), (0.0 - temp_77), temp_77);
        temp_118 = temp_77;
        temp_119 = temp_76;
        temp_120 = temp_78;
        temp_107 = temp_125;
        temp_121 = temp_134.x * fma(temp_101, temp_132, temp_133);
        temp_122 = temp_134.z * fma(temp_103, temp_132, temp_133);
        temp_123 = temp_134.y * fma(temp_102, temp_132, temp_133);
        temp_124 = clamp(fma(temp_135, clamp(temp_33 * -7.0, 0.0, 1.0), (0.0 - temp_135)) + 1.16, 0.0, 1.0);
    }
    temp_136 = temp_118;
    temp_137 = temp_119;
    temp_138 = temp_120;
    temp_139 = temp_108;
    temp_140 = temp_109;
    temp_141 = temp_110;
    temp_142 = temp_124;
    temp_143 = temp_89 + (0.0 - Env.data[23].x);
    temp_144 = in_attr3.x;
    temp_145 = temp_90 + (0.0 - Env.data[23].y);
    temp_146 = in_attr3.z;
    temp_147 = temp_91 + (0.0 - Env.data[23].z);
    temp_148 = fma(temp_75, 0.5, 0.5);
    temp_149 = temp_75 * temp_75;
    temp_150 = temp_95.x * temp_96 * 32.0;
    temp_151 = temp_95.y * temp_96 * 32.0;
    temp_152 = inversesqrt(fma(temp_147, temp_147, fma(temp_145, temp_145, temp_143 * temp_143)));
    temp_153 = temp_143 * temp_152;
    temp_154 = temp_145 * temp_152;
    temp_155 = temp_147 * temp_152;
    temp_156 = temp_136 * temp_137;
    temp_157 = temp_138 * temp_136;
    temp_158 = max(fma(temp_91, temp_155, fma(temp_90, temp_154, temp_89 * temp_153)), 1E-08);
    temp_159 = temp_138 * temp_138;
    temp_160 = temp_149 * temp_149;
    temp_161 = max(fma(temp_155, temp_78, fma(temp_154, temp_77, temp_153 * temp_76)), 1E-08) * max(fma(temp_155, temp_78, fma(temp_154, temp_77, temp_153 * temp_76)), 1E-08);
    temp_162 = uint(max(0, min(int(trunc((temp_146 + (0.0 - BlitzUBO2.data[0x226].z)) * BlitzUBO2.data[0x227].z)), 19)) * 20 + max(0, min(int(trunc((temp_144 + (0.0 - BlitzUBO2.data[0x226].x)) * BlitzUBO2.data[0x227].x)), 19)) << 4) >> 2;
    temp_163 = BlitzUBO2.data[int(temp_162 >> 2)][int(temp_162) & 3];
    temp_164 = temp_148 * 0.5 * temp_148;
    temp_165 = max(fma(temp_78, (0.0 - Env.data[23].z), fma(temp_77, (0.0 - Env.data[23].y), temp_76 * (0.0 - Env.data[23].x))), 1E-08);
    temp_166 = temp_138 * temp_137;
    temp_167 = 1.0 / (temp_164 + fma(temp_107, (0.0 - temp_164), temp_107));
    temp_168 = fma(temp_137, temp_137, (0.0 - temp_136 * temp_136));
    temp_169 = exp2(temp_158 * fma(temp_158, -5.55473, -6.98316002));
    temp_170 = fma(temp_99, (0.0 - temp_140), temp_99);
    temp_171 = temp_167 * (1.0 / (temp_164 + fma(temp_164, (0.0 - temp_165), temp_165))) * temp_149 * (1.0 / max(fma(temp_161, temp_160, (0.0 - temp_161)) + 1.0, 1E-08)) * temp_149 * (1.0 / max(fma(temp_161, temp_160, (0.0 - temp_161)) + 1.0, 1E-08));
    temp_172 = fma(temp_98, (0.0 - temp_139), temp_98);
    temp_173 = fma(temp_104, (0.0 - temp_141), temp_104);
    temp_174 = temp_95.z * temp_96 * 32.0;
    temp_175 = fma(temp_170, temp_151, fma(max(0.0, fma(temp_168, Env.data[31].y, fma(temp_138, Env.data[26].z, fma(temp_136, Env.data[26].y, temp_137 * Env.data[26].x)) + Env.data[26].w + fma(temp_166, Env.data[29].w, fma(temp_159, Env.data[29].z, fma(temp_157, Env.data[29].y, temp_156 * Env.data[29].x))))), temp_170, temp_123));
    temp_176 = fma(temp_172, temp_150, fma(max(0.0, fma(temp_168, Env.data[31].x, fma(temp_138, Env.data[25].z, fma(temp_136, Env.data[25].y, temp_137 * Env.data[25].x)) + Env.data[25].w + fma(temp_166, Env.data[28].w, fma(temp_159, Env.data[28].z, fma(temp_157, Env.data[28].y, temp_156 * Env.data[28].x))))), temp_172, temp_121));
    temp_177 = fma(temp_173, temp_174, fma(max(0.0, fma(temp_168, Env.data[31].z, fma(temp_138, Env.data[27].z, fma(temp_136, Env.data[27].y, temp_137 * Env.data[27].x)) + Env.data[27].w + fma(temp_166, Env.data[30].w, fma(temp_159, Env.data[30].z, fma(temp_157, Env.data[30].y, temp_156 * Env.data[30].x))))), temp_173, temp_122));
    temp_178 = temp_176;
    temp_179 = temp_175;
    temp_180 = temp_177;
    temp_181 = temp_176;
    temp_182 = temp_175;
    temp_183 = temp_177;
    if (floatBitsToInt(temp_163) != -1)
    {
        temp_184 = floatBitsToInt(temp_163);
        temp_185 = 0;
        do
        {
            temp_186 = temp_184;
            temp_187 = temp_178;
            temp_188 = temp_179;
            temp_189 = temp_180;
            temp_190 = temp_186 & 255;
            temp_181 = temp_187;
            temp_182 = temp_188;
            temp_183 = temp_189;
            temp_191 = uint(temp_190) >= 30u;
            if (temp_191)
            {
                break;
            }
            temp_192 = temp_190 << 4;
            temp_193 = uint(temp_192 + 0x1CC0) >> 2;
            temp_194 = int(temp_193) + 1;
            temp_195 = uint(temp_192 + 0x1CC8) >> 2;
            temp_196 = (0.0 - temp_144) + BlitzUBO2.data[int(temp_193 >> 2)][int(temp_193) & 3];
            temp_197 = BlitzUBO2.data[int(uint(temp_194) >> 2)][temp_194 & 3] + (0.0 - in_attr3.y);
            temp_198 = (0.0 - temp_146) + BlitzUBO2.data[int(temp_195 >> 2)][int(temp_195) & 3];
            temp_199 = fma(temp_198, temp_198, fma(temp_197, temp_197, temp_196 * temp_196));
            temp_200 = temp_196 * inversesqrt(temp_199);
            temp_201 = temp_197 * inversesqrt(temp_199);
            temp_202 = temp_198 * inversesqrt(temp_199);
            temp_203 = temp_89 + temp_200;
            temp_204 = temp_90 + temp_201;
            temp_205 = temp_91 + temp_202;
            temp_206 = uint(temp_192 + 0x1AE0) >> 2;
            temp_207 = int(temp_206) + 1;
            temp_208 = inversesqrt(fma(temp_205, temp_205, fma(temp_204, temp_204, temp_203 * temp_203)));
            temp_209 = temp_203 * temp_208;
            temp_210 = temp_204 * temp_208;
            temp_211 = temp_205 * temp_208;
            temp_212 = fma(temp_202, temp_78, fma(temp_201, temp_77, temp_200 * temp_76));
            temp_213 = max(temp_212, 1E-08);
            temp_214 = uint(temp_192 + 0x2080) >> 2;
            temp_215 = max(fma(temp_91, temp_211, fma(temp_90, temp_210, temp_89 * temp_209)), 1E-08);
            temp_216 = max(fma(temp_211, temp_78, fma(temp_210, temp_77, temp_209 * temp_76)), 1E-08) * max(fma(temp_211, temp_78, fma(temp_210, temp_77, temp_209 * temp_76)), 1E-08);
            temp_217 = uint(temp_192 + 0x1908) >> 2;
            temp_218 = uint(temp_192 + 0x1900) >> 2;
            temp_219 = int(temp_218) + 1;
            temp_220 = exp2(temp_215 * fma(temp_215, -5.55473, -6.98316002));
            temp_221 = floatBitsToInt(BlitzUBO2.data[int(temp_214 >> 2)][int(temp_214) & 3]) != 0;
            temp_222 = temp_167 * (1.0 / (temp_164 + fma(temp_164, (0.0 - temp_213), temp_213))) * temp_149 * (1.0 / max(fma(temp_160, temp_216, (0.0 - temp_216)) + 1.0, 1E-08)) * temp_149 * (1.0 / max(fma(temp_160, temp_216, (0.0 - temp_216)) + 1.0, 1E-08));
            temp_223 = fma(temp_220, (0.0 - temp_141), temp_220) + temp_141;
            temp_224 = temp_223;
            if (!temp_221)
            {
                temp_224 = 1.0;
            }
            temp_225 = temp_224;
            if (temp_221)
            {
                temp_226 = uint(temp_192 + 0x1EA0) >> 2;
                temp_227 = int(temp_226) + 1;
                temp_228 = uint(temp_192 + 0x1AE8) >> 2;
                temp_229 = BlitzUBO2.data[int(temp_228 >> 2)][int(temp_228) & 3];
                temp_230 = int(temp_228) + 1;
                temp_231 = uint(temp_192 + 0x1EA8) >> 2;
                temp_225 = exp2(BlitzUBO2.data[int(uint(temp_230) >> 2)][temp_230 & 3] * log2(clamp(((0.0 - temp_229) + fma(temp_202, (0.0 - BlitzUBO2.data[int(temp_231 >> 2)][int(temp_231) & 3]), fma(temp_201, (0.0 - BlitzUBO2.data[int(uint(temp_227) >> 2)][temp_227 & 3]), temp_200 * (0.0 - BlitzUBO2.data[int(temp_226 >> 2)][int(temp_226) & 3])))) * (1.0 / ((0.0 - temp_229) + 1.0)), 0.0, 1.0)));
            }
            temp_232 = temp_185 + 1;
            temp_233 = exp2(BlitzUBO2.data[int(uint(temp_207) >> 2)][temp_207 & 3] * log2(clamp(fma(BlitzUBO2.data[int(temp_206 >> 2)][int(temp_206) & 3], (0.0 - sqrt(temp_199)), 1.0), 0.0, 1.0))) * temp_225 * clamp(temp_212 + -0.0, 0.0, 1.0);
            temp_234 = fma(BlitzUBO2.data[int(temp_218 >> 2)][int(temp_218) & 3] * temp_233, fma(temp_98, 0.31830987, (fma(temp_220, (0.0 - temp_139), temp_220) + temp_139) * temp_222 * 0.0795774683), temp_187);
            temp_235 = fma(BlitzUBO2.data[int(uint(temp_219) >> 2)][temp_219 & 3] * temp_233, fma(temp_99, 0.31830987, (fma(temp_220, (0.0 - temp_140), temp_220) + temp_140) * temp_222 * 0.0795774683), temp_188);
            temp_236 = fma(BlitzUBO2.data[int(temp_217 >> 2)][int(temp_217) & 3] * temp_233, fma(temp_104, 0.31830987, temp_223 * temp_222 * 0.0795774683), temp_189);
            temp_184 = int(uint(temp_186) >> 8);
            temp_185 = temp_232;
            temp_178 = temp_234;
            temp_179 = temp_235;
            temp_180 = temp_236;
            temp_181 = temp_234;
            temp_182 = temp_235;
            temp_183 = temp_236;
        }
        while (!(temp_232 >= 4));
    }
    temp_191 = false;
    temp_237 = temp_144 + (0.0 - Context.data[11].w);
    temp_238 = in_attr3.y;
    temp_239 = temp_146 + (0.0 - Context.data[13].w);
    temp_240 = clamp(fma(temp_78, (0.0 - Env.data[23].z), fma(temp_77, (0.0 - Env.data[23].y), temp_76 * (0.0 - Env.data[23].x))), 0.0, 1.0);
    temp_241 = temp_238 + (0.0 - Context.data[12].w);
    temp_242 = fma(temp_239, temp_239, fma(temp_241, temp_241, temp_237 * temp_237));
    temp_243 = clamp(fma(temp_106 * temp_105, BlitzUBO0.data[54].w, 1.0 + (0.0 - BlitzUBO0.data[54].w)), 0.0, 1.0);
    temp_244 = clamp(fma(fma(temp_146, Env.data[14].z, fma(temp_238, Env.data[14].y, temp_144 * Env.data[14].x)), (0.0 - Env.data[15].x), Env.data[14].w), 0.0, 1.0) * Env.data[13].w;
    temp_245 = fma(temp_105, temp_181, temp_106 * fma((fma(temp_169, (0.0 - temp_139), temp_169) + temp_139) * temp_171, 0.07957747, temp_98 * 0.318309873) * fma(temp_240, Env.data[5].x, temp_150) * temp_142) + temp_72;
    temp_246 = exp2(log2(clamp(sqrt(temp_242) * Context.data[15].x, 0.0, 1.0)) * BlitzUBO0.data[54].x) * exp2(fma(fma(temp_239 * inversesqrt(temp_242), Env.data[23].z, fma(temp_241 * inversesqrt(temp_242), Env.data[23].y, temp_237 * inversesqrt(temp_242) * Env.data[23].x)), (0.0 - BlitzUBO0.data[54].y), BlitzUBO0.data[54].y));
    temp_247 = fma(temp_105, temp_182, temp_106 * fma((fma(temp_169, (0.0 - temp_140), temp_169) + temp_140) * temp_171, 0.07957747, temp_99 * 0.318309873) * fma(temp_240, Env.data[5].y, temp_151) * temp_142) + temp_73;
    temp_248 = fma(temp_105, temp_183, temp_106 * fma((fma(temp_169, (0.0 - temp_141), temp_169) + temp_141) * temp_171, 0.07957747, temp_104 * 0.318309873) * fma(temp_240, Env.data[5].z, temp_174) * temp_142) + temp_74;
    temp_249 = fma((0.0 - temp_245) + Env.data[13].x, temp_244, temp_245);
    temp_250 = fma((0.0 - temp_247) + Env.data[13].y, temp_244, temp_247);
    temp_251 = fma((0.0 - temp_248) + Env.data[13].z, temp_244, temp_248);
    temp_252 = clamp((0.0 - exp2(clamp(fma(sqrt(temp_242), Env.data[12].x, Env.data[11].w), 0.0, 1.0) * (0.0 - BlitzUBO0.data[53].x) * 1.44269502)) + 1.0, 0.0, 1.0) * Env.data[10].w;
    output_color[0].x = fma((0.0 - temp_249) + fma(fma(temp_246 * BlitzUBO0.data[55].x * temp_243, BlitzUBO0.data[54].z, (0.0 - Env.data[10].x)), BlitzUBO0.data[53].w, Env.data[10].x), temp_252, temp_249);
    output_color[0].y = fma((0.0 - temp_250) + fma(fma(temp_246 * BlitzUBO0.data[55].y * temp_243, BlitzUBO0.data[54].z, (0.0 - Env.data[10].y)), BlitzUBO0.data[53].w, Env.data[10].y), temp_252, temp_250);
    output_color[0].z = fma((0.0 - temp_251) + fma(fma(temp_246 * BlitzUBO0.data[55].z * temp_243, BlitzUBO0.data[54].z, (0.0 - Env.data[10].z)), BlitzUBO0.data[53].w, Env.data[10].z), temp_252, temp_251);
    output_color[0].w = 1.0;
    return;
}
