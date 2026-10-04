// Hoian_UBER.Product.bfsha model hoian_uber program 3443 (frag)
// sampler cEnvBRDFMap -> loc 24 -> material sampler ?
// sampler cGSysProjection0 -> loc 16 -> material sampler gsys_projection0
// sampler cGSysShadowPrePass -> loc 17 -> material sampler gsys_shadow_prepass
// sampler cPrefilEnvMapArray -> loc 23 -> material sampler ?
// sampler cTexAlbedo -> loc 1 -> material sampler _a0
// sampler cTexCompPaint -> loc 12 -> material sampler _cp0
// sampler cTexEmission -> loc 6 -> material sampler _e0
// sampler cTexMetalness -> loc 5 -> material sampler _m0
// sampler cTexNormal -> loc 3 -> material sampler _n0
// sampler cTexRoughness -> loc 4 -> material sampler _r0
// sampler cTexSubstitution -> loc 2 -> material sampler _su0
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

layout (binding = 6, std140) uniform _Mat
{
    precise vec4 data[4096];
} Mat;

layout (binding = 7, std140) uniform _BlitzUBO0
{
    precise vec4 data[4096];
} BlitzUBO0;

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

layout (binding = 0) uniform sampler2D cTexNormal;
layout (binding = 1) uniform sampler2D cTexCompPaint;
layout (binding = 2) uniform sampler2D cTexAlbedo;
layout (binding = 3) uniform sampler2D cTexEmission;
layout (binding = 4) uniform sampler2D cGSysShadowPrePass;
layout (binding = 5) uniform sampler2D cTexSubstitution;
layout (binding = 6) uniform sampler2D cTexRoughness;
layout (binding = 7) uniform sampler2D cTexMetalness;
layout (binding = 8) uniform sampler2D cGSysProjection0;
layout (binding = 9) uniform sampler2D cEnvBRDFMap;
layout (binding = 10) uniform samplerCubeArray cPrefilEnvMapArray;
layout (location = 0) in vec4 in_attr0;
layout (location = 1) in vec4 in_attr1;
layout (location = 2) in vec4 in_attr2;
layout (location = 3) in vec4 in_attr3;
layout (location = 4) in vec4 in_attr4;
layout (location = 5) in vec4 in_attr5;
layout (location = 6) in vec4 in_attr6;

layout (location = 0) out vec4 output_color[0];


void main()
{
    precise float temp_0;
    precise float temp_1;
    precise vec2 temp_2;
    precise float temp_3;
    precise float temp_4;
    precise float temp_5;
    precise vec3 temp_6;
    precise float temp_7;
    precise float temp_8;
    precise float temp_9;
    precise vec3 temp_10;
    precise vec3 temp_11;
    precise vec2 temp_12;
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
    int temp_32;
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
    precise float temp_50;
    precise float temp_51;
    bool temp_52;
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
    precise float temp_103;
    precise float temp_104;
    precise float temp_105;
    precise float temp_106;
    precise float temp_107;
    precise float temp_108;
    precise vec2 temp_109;
    precise float temp_110;
    precise float temp_111;
    precise float temp_112;
    precise float temp_113;
    precise float temp_114;
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
    precise float temp_125;
    precise float temp_126;
    precise float temp_127;
    precise float temp_128;
    precise float temp_129;
    precise vec3 temp_130;
    precise float temp_131;
    precise float temp_132;
    precise float temp_133;
    precise float temp_134;
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
    precise vec2 temp_146;
    precise float temp_147;
    precise float temp_148;
    precise vec3 temp_149;
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
    precise float temp_184;
    uint temp_185;
    precise float temp_186;
    precise float temp_187;
    precise float temp_188;
    precise float temp_189;
    precise float temp_190;
    precise float temp_191;
    precise float temp_192;
    precise float temp_193;
    int temp_194;
    precise float temp_195;
    precise float temp_196;
    precise float temp_197;
    precise float temp_198;
    precise float temp_199;
    precise float temp_200;
    precise float temp_201;
    precise float temp_202;
    precise float temp_203;
    int temp_204;
    int temp_205;
    precise float temp_206;
    precise float temp_207;
    precise float temp_208;
    int temp_209;
    bool temp_210;
    int temp_211;
    uint temp_212;
    int temp_213;
    uint temp_214;
    precise float temp_215;
    precise float temp_216;
    precise float temp_217;
    uint temp_218;
    precise float temp_219;
    precise float temp_220;
    precise float temp_221;
    precise float temp_222;
    precise float temp_223;
    precise float temp_224;
    precise float temp_225;
    precise float temp_226;
    bool temp_227;
    precise float temp_228;
    precise float temp_229;
    precise float temp_230;
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
    uint temp_242;
    int temp_243;
    uint temp_244;
    precise float temp_245;
    int temp_246;
    uint temp_247;
    uint temp_248;
    int temp_249;
    int temp_250;
    uint temp_251;
    int temp_252;
    precise float temp_253;
    precise float temp_254;
    precise float temp_255;
    precise float temp_256;
    precise float temp_257;
    precise float temp_258;
    precise float temp_259;
    precise float temp_260;
    precise float temp_261;
    precise float temp_262;
    precise float temp_263;
    precise float temp_264;
    precise float temp_265;
    precise float temp_266;
    precise float temp_267;
    precise float temp_268;
    precise float temp_269;
    precise float temp_270;
    precise float temp_271;
    precise float temp_272;
    precise float temp_273;
    precise float temp_274;
    precise float temp_275;
    temp_210 = false;
    temp_0 = in_attr0.x;
    temp_1 = in_attr0.y;
    temp_2 = texture(cTexNormal, vec2(temp_0, temp_1)).xy;
    temp_3 = temp_2.x;
    temp_4 = temp_2.y;
    temp_5 = 1.0 / in_attr5.w;
    temp_6 = texture(cTexAlbedo, vec2(temp_0, temp_1)).xyz;
    temp_7 = temp_6.x;
    temp_8 = temp_6.y;
    temp_9 = temp_6.z;
    temp_10 = texture(cTexEmission, vec2(temp_0, temp_1)).xyz;
    temp_11 = texture(cTexEmission, vec2(temp_0, temp_1)).xyz;
    temp_12 = texture(cGSysShadowPrePass, vec2(fma(in_attr5.x * temp_5, 0.5, 0.5), fma(in_attr5.y * temp_5, -0.5, 0.5))).xy;
    temp_13 = in_attr1.x;
    temp_14 = in_attr1.y;
    temp_15 = in_attr1.z;
    temp_16 = in_attr2.y;
    temp_17 = in_attr2.z;
    temp_18 = in_attr2.x;
    temp_19 = in_attr2.w;
    temp_20 = inversesqrt(fma(temp_15, temp_15, fma(temp_14, temp_14, temp_13 * temp_13)));
    temp_21 = temp_15 * temp_20;
    temp_22 = temp_13 * temp_20;
    temp_23 = temp_14 * temp_20;
    temp_24 = texture(cTexCompPaint, vec2(temp_0 + Mat.comp_paint_texcoord_offset, temp_1 + Mat.comp_paint_texcoord_offset)).x + (0.0 - texture(cTexCompPaint, vec2(temp_0 + (0.0 - Mat.comp_paint_texcoord_offset), temp_1 + (0.0 - Mat.comp_paint_texcoord_offset))).x);
    temp_25 = sqrt(clamp((0.0 - fma(temp_3, temp_3, temp_4 * temp_4)) + 1.0, 0.0, 1.0));
    temp_26 = fma(temp_22, temp_25, fma(temp_3, temp_18, temp_4 * fma(temp_23, temp_17, (0.0 - temp_21 * temp_16)) * temp_19));
    temp_27 = fma(temp_23, temp_25, fma(temp_3, temp_16, temp_4 * fma(temp_21, temp_18, (0.0 - temp_22 * temp_17)) * temp_19));
    temp_28 = fma(temp_21, temp_25, fma(temp_3, temp_17, temp_4 * fma(temp_22, temp_16, (0.0 - temp_23 * temp_18)) * temp_19));
    temp_29 = fma(temp_17 * temp_24, Mat.comp_paint_norm_intens, temp_21);
    temp_30 = inversesqrt(fma(temp_28, temp_28, fma(temp_27, temp_27, temp_26 * temp_26)));
    temp_31 = fma((0.0 - BlitzUBO0.data[20].y) + BlitzUBO0.data[20].x, clamp(temp_23 + -0.0, 0.0, 1.0), BlitzUBO0.data[20].y);
    temp_32 = (0 - floatBitsToInt(Mat.two_comp_paint_team)) + 1;
    temp_33 = temp_27 * temp_30;
    temp_34 = fma(temp_16 * temp_24, Mat.comp_paint_norm_intens, temp_23);
    temp_35 = fma(temp_18 * temp_24, Mat.comp_paint_norm_intens, temp_22);
    temp_36 = temp_26 * temp_30;
    temp_37 = temp_28 * temp_30;
    temp_38 = min(texture(cTexCompPaint, vec2(temp_0, temp_1)).x + Mat.two_color_complement_paint_intensity + -1.0, 0.3) + BlitzUBO0.data[21].w;
    temp_39 = temp_38 * float(max(0, temp_32));
    temp_40 = inversesqrt(fma(temp_29, temp_29, fma(temp_34, temp_34, temp_35 * temp_35)));
    temp_41 = temp_38 * float(max(0, (0 - temp_32)));
    temp_42 = temp_38 * float((0 - abs(temp_32)) + 1);
    temp_43 = temp_35 * temp_40;
    temp_44 = temp_29 * temp_40;
    temp_45 = temp_34 * temp_40;
    temp_46 = max(temp_41, max(temp_42, temp_39));
    temp_47 = temp_46 + (0.0 - BlitzUBO0.data[21].w);
    temp_48 = clamp(temp_47 + -0.0, 0.0, 1.0);
    temp_49 = clamp((temp_42 + (0.0 - temp_46) + 9.99999975E-05) * 100000000.0, 0.0, 1.0);
    temp_50 = clamp((temp_39 + (0.0 - temp_46) + 9.99999975E-05) * 100000000.0, 0.0, 1.0);
    temp_51 = clamp((temp_41 + (0.0 - temp_46) + 9.99999975E-05) * 100000000.0, 0.0, 1.0);
    temp_52 = min(temp_48 * 1000.0, 1.0) > 0.5;
    temp_53 = temp_36;
    temp_54 = temp_33;
    temp_55 = temp_37;
    if (temp_52)
    {
        temp_56 = fma(temp_51, BlitzUBO0.data[62].y, fma(temp_50, BlitzUBO0.data[3].y, temp_49 * BlitzUBO0.data[10].y));
        temp_57 = fma(temp_51, BlitzUBO0.data[62].z, fma(temp_50, BlitzUBO0.data[3].z, temp_49 * BlitzUBO0.data[10].z));
        temp_58 = fma(temp_51, BlitzUBO0.data[62].x, fma(temp_50, BlitzUBO0.data[3].x, temp_49 * BlitzUBO0.data[10].x));
        temp_59 = fma(temp_51, BlitzUBO0.data[63].x, fma(temp_50, BlitzUBO0.data[4].x, temp_49 * BlitzUBO0.data[11].x));
        temp_60 = fma(temp_51, BlitzUBO0.data[63].y, fma(temp_50, BlitzUBO0.data[4].y, temp_49 * BlitzUBO0.data[11].y));
        temp_61 = fma(temp_51, BlitzUBO0.data[63].z, fma(temp_50, BlitzUBO0.data[4].z, temp_49 * BlitzUBO0.data[11].z));
        temp_62 = clamp(temp_48 * BlitzUBO0.data[45].z, 0.0, 1.0);
        temp_63 = fma(fma(temp_59, (0.0 - BlitzUBO0.data[45].y), temp_58), temp_62, temp_59 * BlitzUBO0.data[45].y);
        temp_64 = fma(fma(temp_60, (0.0 - BlitzUBO0.data[45].y), temp_56), temp_62, temp_60 * BlitzUBO0.data[45].y);
        temp_65 = fma(fma(temp_61, (0.0 - BlitzUBO0.data[45].y), temp_57), temp_62, temp_61 * BlitzUBO0.data[45].y);
        temp_66 = BlitzUBO0.data[18].w;
        temp_67 = temp_63;
        temp_68 = temp_64;
        temp_69 = 0.0;
        temp_53 = fma(temp_31, (0.0 - temp_36) + temp_43, temp_36);
        temp_54 = fma(temp_31, (0.0 - temp_33) + temp_45, temp_33);
        temp_55 = fma(temp_31, (0.0 - temp_37) + temp_44, temp_37);
        temp_70 = temp_65;
        temp_71 = 0.0;
        temp_72 = temp_56;
        temp_73 = temp_58;
        temp_74 = temp_57;
        temp_75 = temp_10.y * Mat.emission_color.y;
        temp_76 = temp_10.x * Mat.emission_color.x;
        temp_77 = temp_10.z * Mat.emission_color.z;
        temp_78 = temp_63 * BlitzUBO0.data[18].z;
        temp_79 = temp_64 * BlitzUBO0.data[18].z;
        temp_80 = temp_65 * BlitzUBO0.data[18].z;
    }
    else
    {
        temp_81 = clamp(texture(cTexSubstitution, vec2(temp_0, temp_1)).x + Mat.team_color_blend_alpha, 0.0, 1.0);
        temp_82 = fma((0.0 - temp_7) + Mat.my_team_color.x, temp_81, temp_7);
        temp_83 = fma((0.0 - temp_8) + Mat.my_team_color.y, temp_81, temp_8);
        temp_84 = fma((0.0 - temp_9) + Mat.my_team_color.z, temp_81, temp_9);
        temp_66 = max(texture(cTexRoughness, vec2(temp_0, temp_1)).x, 0.0001);
        temp_67 = temp_82;
        temp_68 = temp_83;
        temp_69 = texture(cTexMetalness, vec2(temp_0, temp_1)).x;
        temp_70 = temp_84;
        temp_71 = 1.0;
        temp_72 = temp_83 * Mat.transmission_color_backlight.y;
        temp_73 = temp_82 * Mat.transmission_color_backlight.x;
        temp_74 = temp_84 * Mat.transmission_color_backlight.z;
        temp_75 = temp_11.y * Mat.emission_color.y;
        temp_76 = temp_11.x * Mat.emission_color.x;
        temp_77 = temp_11.z * Mat.emission_color.z;
        temp_78 = 0.0;
        temp_79 = 0.0;
        temp_80 = 0.0;
    }
    temp_85 = temp_66;
    temp_86 = temp_67;
    temp_87 = temp_68;
    temp_88 = temp_69;
    temp_89 = temp_53;
    temp_90 = temp_54;
    temp_91 = temp_55;
    temp_92 = temp_70;
    temp_93 = temp_71;
    temp_94 = temp_72;
    temp_95 = temp_73;
    temp_96 = temp_74;
    temp_97 = in_attr4.x;
    temp_98 = in_attr4.y;
    temp_99 = (0.0 - temp_12.y) + 1.0;
    temp_100 = in_attr4.z;
    temp_101 = 1.0 / (in_attr6.z * gl_FragCoord.w);
    temp_102 = fma(temp_86 + -0.0399999991, temp_88, 0.04);
    temp_103 = inversesqrt(fma(temp_100, temp_100, fma(temp_98, temp_98, temp_97 * temp_97)));
    temp_104 = temp_97 * (0.0 - temp_103);
    temp_105 = temp_98 * (0.0 - temp_103);
    temp_106 = temp_100 * (0.0 - temp_103);
    temp_107 = fma(temp_106, temp_91, fma(temp_105, temp_90, temp_104 * temp_89));
    temp_108 = max(temp_107, 1E-08);
    temp_109 = texture(cEnvBRDFMap, vec2(temp_108, (0.0 - temp_85) + -0.0)).xy;
    temp_110 = fma(temp_86, (0.0 - temp_88), temp_86);
    temp_111 = fma(temp_87, (0.0 - temp_88), temp_87);
    temp_112 = fma(temp_92, (0.0 - temp_88), temp_92);
    temp_113 = fma(temp_87 + -0.0399999991, temp_88, 0.04);
    temp_114 = fma(temp_92 + -0.0399999991, temp_88, 0.04);
    temp_115 = clamp(in_attr3.w + BlitzUBO0.data[36].z, 0.0, 1.0);
    temp_116 = temp_99 * temp_115;
    temp_117 = clamp((0.0 - fma(max((0.0 - temp_12.x) + 1.0, temp_99), temp_115, fma(texture(cGSysProjection0, vec2(in_attr6.x * gl_FragCoord.w * temp_101, in_attr6.y * gl_FragCoord.w * temp_101)).x, (0.0 - Context.data[41].x), Context.data[41].x))) + 1.0, 0.0, 1.0);
    temp_118 = temp_108;
    temp_119 = temp_111;
    temp_120 = temp_102;
    temp_121 = temp_113;
    temp_122 = temp_114;
    temp_123 = temp_110;
    temp_124 = temp_112;
    if (temp_52)
    {
        temp_125 = fma(temp_106, (0.0 - temp_91), fma(temp_105, (0.0 - temp_90), temp_104 * (0.0 - temp_89)));
        temp_126 = fma(temp_125 * temp_89, -2.0, (0.0 - temp_104));
        temp_127 = fma(temp_125 * temp_90, -2.0, (0.0 - temp_105));
        temp_128 = fma(temp_125 * temp_91, -2.0, (0.0 - temp_106));
        temp_129 = 1.0 / max(abs(temp_128), max(abs(temp_126), abs(temp_127)));
        temp_130 = texture(cPrefilEnvMapArray, vec4(temp_126 * temp_129, temp_127 * temp_129, temp_128 * temp_129, float(12)), 0.0).xyz;
        temp_131 = fma(temp_109.x, BlitzUBO0.data[19].x, temp_109.y);
        temp_132 = temp_89 * BlitzUBO0.data[19].z;
        temp_133 = fma(temp_90 + -1.0, BlitzUBO0.data[19].z, 1.0);
        temp_134 = temp_91 * BlitzUBO0.data[19].z;
        temp_120 = BlitzUBO0.data[19].x;
        temp_121 = BlitzUBO0.data[19].x;
        temp_122 = BlitzUBO0.data[19].x;
        temp_135 = temp_130.x * temp_131;
        temp_136 = temp_130.y * temp_131;
        temp_137 = temp_130.z * temp_131;
        temp_138 = 0.0;
        temp_139 = 1.0;
    }
    else
    {
        temp_140 = max(temp_107, 1E-08);
        temp_141 = fma(temp_106, (0.0 - temp_91), fma(temp_105, (0.0 - temp_90), temp_104 * (0.0 - temp_89)));
        temp_142 = fma(temp_141 * temp_89, -2.0, (0.0 - temp_104));
        temp_143 = fma(temp_141 * temp_90, -2.0, (0.0 - temp_105));
        temp_144 = fma(temp_141 * temp_91, -2.0, (0.0 - temp_106));
        temp_145 = 1.0 / max(abs(temp_144), max(abs(temp_142), abs(temp_143)));
        temp_146 = texture(cEnvBRDFMap, vec2(temp_140, (0.0 - temp_85) + -0.0)).xy;
        temp_147 = temp_146.x;
        temp_148 = temp_146.y;
        temp_149 = texture(cPrefilEnvMapArray, vec4(temp_142 * temp_145, temp_143 * temp_145, temp_144 * temp_145, float(int(clamp(uint(max(roundEven(roundEven(fma(cos(temp_85 * 3.14159274), -5.5, 5.5))), 0.0)), 0u, 0xFFFFu))))).xyz;
        temp_150 = temp_104 * temp_105;
        temp_151 = temp_105 * temp_106;
        temp_152 = temp_106 * temp_106;
        temp_153 = temp_104 * temp_106;
        temp_154 = fma(temp_104, temp_104, (0.0 - temp_105 * temp_105));
        temp_155 = exp2(log2(clamp((0.0 - temp_107) + 1.0, 0.0, 1.0)) * Mat.edge_light_power.x) * Mat.edge_light_intens;
        temp_156 = fma(fma(temp_44, (0.0 - Env.data[23].z), fma(temp_45, (0.0 - Env.data[23].y), temp_43 * (0.0 - Env.data[23].x))), (0.0 - temp_90), temp_90);
        temp_132 = temp_89;
        temp_133 = temp_90;
        temp_134 = temp_91;
        temp_118 = temp_140;
        temp_119 = fma(max(0.0, fma(temp_154, Env.data[31].y, fma(temp_106, (0.0 - Env.data[26].z), fma(temp_105, (0.0 - Env.data[26].y), temp_104 * (0.0 - Env.data[26].x))) + Env.data[26].w + fma(temp_153, Env.data[29].w, fma(temp_152, Env.data[29].z, fma(temp_151, Env.data[29].y, temp_150 * Env.data[29].x))))) * Mat.edge_light_color.y * temp_155, temp_93, temp_111);
        temp_123 = fma(max(0.0, fma(temp_154, Env.data[31].x, fma(temp_106, (0.0 - Env.data[25].z), fma(temp_105, (0.0 - Env.data[25].y), temp_104 * (0.0 - Env.data[25].x))) + Env.data[25].w + fma(temp_153, Env.data[28].w, fma(temp_152, Env.data[28].z, fma(temp_151, Env.data[28].y, temp_150 * Env.data[28].x))))) * Mat.edge_light_color.x * temp_155, temp_93, temp_110);
        temp_124 = fma(max(0.0, fma(temp_154, Env.data[31].z, fma(temp_106, (0.0 - Env.data[27].z), fma(temp_105, (0.0 - Env.data[27].y), temp_104 * (0.0 - Env.data[27].x))) + Env.data[27].w + fma(temp_153, Env.data[30].w, fma(temp_152, Env.data[30].z, fma(temp_151, Env.data[30].y, temp_150 * Env.data[30].x))))) * Mat.edge_light_color.z * temp_155, temp_93, temp_112);
        temp_135 = fma(temp_102, temp_147, temp_148) * temp_149.x;
        temp_136 = fma(temp_113, temp_147, temp_148) * temp_149.y;
        temp_137 = fma(temp_114, temp_147, temp_148) * temp_149.z;
        temp_138 = Mat.transmission_rate;
        temp_139 = clamp(fma(temp_156, clamp(temp_47 * -7.0, 0.0, 1.0), (0.0 - temp_156)) + 1.16, 0.0, 1.0);
    }
    temp_157 = temp_132;
    temp_158 = temp_133;
    temp_159 = temp_134;
    temp_160 = temp_119;
    temp_161 = temp_120;
    temp_162 = temp_121;
    temp_163 = temp_122;
    temp_164 = temp_123;
    temp_165 = temp_124;
    temp_166 = temp_138;
    temp_167 = temp_139;
    temp_168 = temp_104 + (0.0 - Env.data[23].x);
    temp_169 = temp_105 + (0.0 - Env.data[23].y);
    temp_170 = temp_106 + (0.0 - Env.data[23].z);
    temp_171 = inversesqrt(fma(temp_170, temp_170, fma(temp_169, temp_169, temp_168 * temp_168)));
    temp_172 = temp_168 * temp_171;
    temp_173 = temp_169 * temp_171;
    temp_174 = temp_170 * temp_171;
    temp_175 = temp_159 * temp_158;
    temp_176 = temp_158 * temp_157;
    temp_177 = fma(temp_85, 0.5, 0.5);
    temp_178 = temp_85 * temp_85;
    temp_179 = temp_177 * 0.5 * temp_177;
    temp_180 = max(fma(temp_174, temp_91, fma(temp_173, temp_90, temp_172 * temp_89)), 1E-08) * max(fma(temp_174, temp_91, fma(temp_173, temp_90, temp_172 * temp_89)), 1E-08);
    temp_181 = max(fma(temp_106, temp_174, fma(temp_105, temp_173, temp_104 * temp_172)), 1E-08);
    temp_182 = temp_178 * temp_178;
    temp_183 = fma(temp_157, temp_157, (0.0 - temp_158 * temp_158));
    temp_184 = temp_159 * temp_157;
    temp_185 = uint(max(0, min(int(trunc((in_attr3.z + (0.0 - BlitzUBO2.data[0x226].z)) * BlitzUBO2.data[0x227].z)), 19)) * 20 + max(0, min(int(trunc((in_attr3.x + (0.0 - BlitzUBO2.data[0x226].x)) * BlitzUBO2.data[0x227].x)), 19)) << 4) >> 2;
    temp_186 = BlitzUBO2.data[int(temp_185 >> 2)][int(temp_185) & 3];
    temp_187 = temp_159 * temp_159;
    temp_188 = 1.0 / (temp_179 + fma(temp_118, (0.0 - temp_179), temp_118));
    temp_189 = exp2(temp_181 * fma(temp_181, -5.55473, -6.98316002));
    temp_190 = temp_188 * (1.0 / (temp_179 + fma(max(fma(temp_91, (0.0 - Env.data[23].z), fma(temp_90, (0.0 - Env.data[23].y), temp_89 * (0.0 - Env.data[23].x))), 1E-08), (0.0 - temp_179), max(fma(temp_91, (0.0 - Env.data[23].z), fma(temp_90, (0.0 - Env.data[23].y), temp_89 * (0.0 - Env.data[23].x))), 1E-08)))) * temp_178 * (1.0 / max(fma(temp_180, temp_182, (0.0 - temp_180)) + 1.0, 1E-08)) * temp_178 * (1.0 / max(fma(temp_180, temp_182, (0.0 - temp_180)) + 1.0, 1E-08));
    temp_191 = fma(max(0.0, fma(temp_183, Env.data[31].x, fma(temp_159, Env.data[25].z, fma(temp_158, Env.data[25].y, temp_157 * Env.data[25].x)) + Env.data[25].w + fma(temp_184, Env.data[28].w, fma(temp_187, Env.data[28].z, fma(temp_175, Env.data[28].y, temp_176 * Env.data[28].x))))), fma(temp_161, (0.0 - temp_164), temp_164), temp_135);
    temp_192 = fma(max(0.0, fma(temp_183, Env.data[31].y, fma(temp_159, Env.data[26].z, fma(temp_158, Env.data[26].y, temp_157 * Env.data[26].x)) + Env.data[26].w + fma(temp_184, Env.data[29].w, fma(temp_187, Env.data[29].z, fma(temp_175, Env.data[29].y, temp_176 * Env.data[29].x))))), fma(temp_162, (0.0 - temp_160), temp_160), temp_136);
    temp_193 = fma(max(0.0, fma(temp_183, Env.data[31].z, fma(temp_159, Env.data[27].z, fma(temp_158, Env.data[27].y, temp_157 * Env.data[27].x)) + Env.data[27].w + fma(temp_184, Env.data[30].w, fma(temp_187, Env.data[30].z, fma(temp_175, Env.data[30].y, temp_176 * Env.data[30].x))))), fma(temp_163, (0.0 - temp_165), temp_165), temp_137);
    temp_194 = floatBitsToInt(temp_186);
    temp_195 = temp_192;
    temp_196 = temp_191;
    temp_197 = temp_193;
    temp_198 = temp_191;
    temp_199 = temp_192;
    temp_200 = temp_193;
    if (floatBitsToInt(temp_186) != -1)
    {
        temp_201 = clamp((0.0 - temp_166) + 1.0, 0.0, 1.0);
        temp_202 = clamp(fma(temp_116, (0.0 - BlitzUBO0.data[36].w), 1.0), 0.0, 1.0);
        temp_203 = (Mat.scattering_rate + -1.0) * (Mat.scattering_rate + -1.0);
        temp_204 = 0;
        do
        {
            temp_205 = temp_194;
            temp_206 = temp_195;
            temp_207 = temp_196;
            temp_208 = temp_197;
            temp_209 = temp_205 & 255;
            temp_198 = temp_207;
            temp_199 = temp_206;
            temp_200 = temp_208;
            temp_210 = uint(temp_209) >= 30u;
            if (temp_210)
            {
                break;
            }
            temp_211 = temp_209 << 4;
            temp_212 = uint(temp_211 + 0x1CC0) >> 2;
            temp_213 = int(temp_212) + 1;
            temp_214 = uint(temp_211 + 0x1CC8) >> 2;
            temp_215 = (0.0 - in_attr3.x) + BlitzUBO2.data[int(temp_212 >> 2)][int(temp_212) & 3];
            temp_216 = BlitzUBO2.data[int(uint(temp_213) >> 2)][temp_213 & 3] + (0.0 - in_attr3.y);
            temp_217 = (0.0 - in_attr3.z) + BlitzUBO2.data[int(temp_214 >> 2)][int(temp_214) & 3];
            temp_218 = uint(temp_211 + 0x2080) >> 2;
            temp_219 = fma(temp_217, temp_217, fma(temp_216, temp_216, temp_215 * temp_215));
            temp_220 = temp_215 * inversesqrt(temp_219);
            temp_221 = temp_216 * inversesqrt(temp_219);
            temp_222 = temp_217 * inversesqrt(temp_219);
            temp_223 = temp_104 + temp_220;
            temp_224 = temp_105 + temp_221;
            temp_225 = temp_106 + temp_222;
            temp_226 = inversesqrt(fma(temp_225, temp_225, fma(temp_224, temp_224, temp_223 * temp_223)));
            temp_227 = floatBitsToInt(BlitzUBO2.data[int(temp_218 >> 2)][int(temp_218) & 3]) != 0;
            temp_228 = temp_223 * temp_226;
            temp_229 = temp_224 * temp_226;
            temp_230 = temp_225 * temp_226;
            temp_231 = uint(temp_211 + 0x1AE0) >> 2;
            temp_232 = int(temp_231) + 1;
            temp_233 = fma(temp_229, temp_90, temp_228 * temp_89);
            temp_234 = temp_233;
            if (!temp_227)
            {
                temp_234 = 1.0;
            }
            temp_235 = max(fma(temp_106, temp_230, fma(temp_105, temp_229, temp_104 * temp_228)), 1E-08);
            temp_236 = fma(temp_222, temp_91, fma(temp_221, temp_90, temp_220 * temp_89));
            temp_237 = max(fma(temp_230, temp_91, temp_233), 1E-08) * max(fma(temp_230, temp_91, temp_233), 1E-08);
            temp_238 = max(temp_236, 1E-08);
            temp_239 = exp2(temp_235 * fma(temp_235, -5.55473, -6.98316002));
            temp_240 = temp_188 * (1.0 / (temp_179 + fma(temp_179, (0.0 - temp_238), temp_238))) * temp_178 * (1.0 / max(fma(temp_182, temp_237, (0.0 - temp_237)) + 1.0, 1E-08)) * temp_178 * (1.0 / max(fma(temp_182, temp_237, (0.0 - temp_237)) + 1.0, 1E-08));
            temp_241 = temp_234;
            if (temp_227)
            {
                temp_242 = uint(temp_211 + 0x1EA0) >> 2;
                temp_243 = int(temp_242) + 1;
                temp_244 = uint(temp_211 + 0x1AE8) >> 2;
                temp_245 = BlitzUBO2.data[int(temp_244 >> 2)][int(temp_244) & 3];
                temp_246 = int(temp_244) + 1;
                temp_247 = uint(temp_211 + 0x1EA8) >> 2;
                temp_241 = exp2(log2(clamp((fma(temp_222, (0.0 - BlitzUBO2.data[int(temp_247 >> 2)][int(temp_247) & 3]), fma(temp_221, (0.0 - BlitzUBO2.data[int(uint(temp_243) >> 2)][temp_243 & 3]), temp_220 * (0.0 - BlitzUBO2.data[int(temp_242 >> 2)][int(temp_242) & 3]))) + (0.0 - temp_245)) * (1.0 / ((0.0 - temp_245) + 1.0)), 0.0, 1.0)) * BlitzUBO2.data[int(uint(temp_246) >> 2)][temp_246 & 3]);
            }
            temp_248 = uint(temp_211 + 0x1908) >> 2;
            temp_249 = int(temp_248) + 1;
            temp_250 = temp_204 + 1;
            temp_251 = uint(temp_211 + 0x1900) >> 2;
            temp_252 = int(temp_251) + 1;
            temp_253 = exp2(BlitzUBO2.data[int(uint(temp_232) >> 2)][temp_232 & 3] * log2(clamp(fma(BlitzUBO2.data[int(temp_231 >> 2)][int(temp_231) & 3], (0.0 - sqrt(temp_219)), 1.0), 0.0, 1.0))) * temp_241;
            temp_254 = temp_253 * clamp(temp_236 + -0.0, 0.0, 1.0);
            temp_255 = temp_253 * BlitzUBO2.data[int(uint(temp_249) >> 2)][temp_249 & 3];
            temp_256 = exp2(log2(clamp(fma(temp_107, (0.0 - clamp((0.0 - temp_236) + -0.0, 0.0, 1.0)), 1.0), 0.0, 1.0)) * Mat.edge_transmission_power.x) * (fma(temp_203, -0.2, exp2(1.0 / Mat.scattering_rate * log2(clamp(max(fma(temp_106, (0.0 - temp_222), fma(temp_105, (0.0 - temp_221), temp_104 * (0.0 - temp_220))), 0.001) + -0.0, 0.0, 1.0))) * temp_203) + 0.200000003);
            temp_257 = fma(temp_254 * BlitzUBO2.data[int(uint(temp_252) >> 2)][temp_252 & 3] * fma(temp_160, 0.31830987, (fma(temp_239, (0.0 - temp_162), temp_239) + temp_162) * temp_240 * 0.0795774683), temp_201, temp_202 * temp_256 * temp_255 * temp_94 * temp_166) + temp_206;
            temp_258 = fma(temp_254 * BlitzUBO2.data[int(temp_251 >> 2)][int(temp_251) & 3] * fma(temp_164, 0.31830987, (fma(temp_239, (0.0 - temp_161), temp_239) + temp_161) * temp_240 * 0.0795774683), temp_201, temp_202 * temp_256 * temp_255 * temp_95 * temp_166) + temp_207;
            temp_259 = fma(temp_254 * BlitzUBO2.data[int(temp_248 >> 2)][int(temp_248) & 3] * fma(temp_165, 0.31830987, (fma(temp_239, (0.0 - temp_163), temp_239) + temp_163) * temp_240 * 0.0795774683), temp_201, temp_202 * temp_256 * temp_255 * temp_96 * temp_166) + temp_208;
            temp_194 = int(uint(temp_205) >> 8);
            temp_204 = temp_250;
            temp_195 = temp_257;
            temp_196 = temp_258;
            temp_197 = temp_259;
            temp_198 = temp_258;
            temp_199 = temp_257;
            temp_200 = temp_259;
        }
        while (!(temp_250 >= 4));
    }
    temp_210 = false;
    temp_260 = in_attr3.x + (0.0 - Context.data[11].w);
    temp_261 = in_attr3.y + (0.0 - Context.data[12].w);
    temp_262 = fma(temp_91, (0.0 - Env.data[23].z), fma(temp_90, (0.0 - Env.data[23].y), temp_89 * (0.0 - Env.data[23].x)));
    temp_263 = clamp(temp_262 + -0.0, 0.0, 1.0);
    temp_264 = (Mat.scattering_rate + -1.0) * (Mat.scattering_rate + -1.0);
    temp_265 = in_attr3.z + (0.0 - Context.data[13].w);
    temp_266 = fma(temp_265, temp_265, fma(temp_261, temp_261, temp_260 * temp_260));
    temp_267 = clamp((0.0 - temp_166) + 1.0, 0.0, 1.0);
    temp_268 = exp2(log2(clamp(fma(temp_107, (0.0 - clamp((0.0 - temp_262) + -0.0, 0.0, 1.0)), 1.0), 0.0, 1.0)) * Mat.edge_transmission_power.x) * (fma(temp_264, -0.2, temp_264 * exp2(1.0 / Mat.scattering_rate * log2(clamp(max(fma(temp_106, Env.data[23].z, fma(temp_105, Env.data[23].y, temp_104 * Env.data[23].x)), 0.001) + -0.0, 0.0, 1.0)))) + 0.200000003);
    temp_269 = clamp(fma(temp_116, (0.0 - BlitzUBO0.data[36].w), 1.0), 0.0, 1.0);
    temp_270 = exp2(log2(clamp(sqrt(temp_266) * Context.data[15].x, 0.0, 1.0)) * BlitzUBO0.data[54].x) * exp2(fma(fma(temp_265 * inversesqrt(temp_266), Env.data[23].z, fma(temp_261 * inversesqrt(temp_266), Env.data[23].y, temp_260 * inversesqrt(temp_266) * Env.data[23].x)), (0.0 - BlitzUBO0.data[54].y), BlitzUBO0.data[54].y));
    temp_271 = clamp(fma(temp_117, BlitzUBO0.data[54].w, 1.0 + (0.0 - BlitzUBO0.data[54].w)), 0.0, 1.0);
    temp_272 = fma(temp_76, Mat.emission_intensity.x, fma(temp_117, temp_263 * Env.data[5].x * fma((fma(temp_189, (0.0 - temp_161), temp_189) + temp_161) * temp_190, 0.07957747, temp_164 * 0.318309873) * temp_267 * temp_167, temp_269 * temp_95 * Env.data[5].w * temp_268 * temp_166) + temp_198) + temp_78;
    temp_273 = fma(temp_75, Mat.emission_intensity.x, fma(temp_117, temp_263 * Env.data[5].y * fma((fma(temp_189, (0.0 - temp_162), temp_189) + temp_162) * temp_190, 0.07957747, temp_160 * 0.318309873) * temp_267 * temp_167, temp_269 * temp_94 * Env.data[5].w * temp_268 * temp_166) + temp_199) + temp_79;
    temp_274 = fma(temp_77, Mat.emission_intensity.x, fma(temp_117, temp_263 * Env.data[5].z * fma((fma(temp_189, (0.0 - temp_163), temp_189) + temp_163) * temp_190, 0.07957747, temp_165 * 0.318309873) * temp_267 * temp_167, temp_269 * temp_96 * Env.data[5].w * temp_268 * temp_166) + temp_200) + temp_80;
    temp_275 = clamp((0.0 - exp2(clamp(fma(sqrt(temp_266), Env.data[12].x, Env.data[11].w), 0.0, 1.0) * (0.0 - BlitzUBO0.data[53].x) * 1.44269502)) + 1.0, 0.0, 1.0) * Env.data[10].w;
    output_color[0].x = fma((0.0 - temp_272) + fma(fma(temp_270 * BlitzUBO0.data[55].x * temp_271, BlitzUBO0.data[54].z, (0.0 - Env.data[10].x)), BlitzUBO0.data[53].w, Env.data[10].x), temp_275, temp_272);
    output_color[0].y = fma((0.0 - temp_273) + fma(fma(temp_270 * BlitzUBO0.data[55].y * temp_271, BlitzUBO0.data[54].z, (0.0 - Env.data[10].y)), BlitzUBO0.data[53].w, Env.data[10].y), temp_275, temp_273);
    output_color[0].z = fma((0.0 - temp_274) + fma(fma(temp_270 * BlitzUBO0.data[55].z * temp_271, BlitzUBO0.data[54].z, (0.0 - Env.data[10].z)), BlitzUBO0.data[53].w, Env.data[10].z), temp_275, temp_274);
    output_color[0].w = 1.0;
    return;
}
