// static_grsn.bfsha model VfxGeneralShader program 1897 (vert)
// sampler sysCustomShaderShadowArraySampler0 -> loc 10 -> material sampler ?
// sampler sysCustomShaderShadowSampler0 -> loc 11 -> material sampler ?
// sampler sysCustomShaderTextureSampler1 -> loc 9 -> material sampler ?
// sampler sysCustomShaderTextureSampler2 -> loc 12 -> material sampler ?
// ubo NnVfx2EmitterDynamicParam -> loc 7 (labelled)
// ubo NnVfx2ViewParam -> loc 5 (labelled)
// ubo sysCustomShaderUniformBlock0 -> loc 11
// ubo sysCustomShaderUniformBlock1 -> loc 12
// ubo sysEmitterStaticUniformBlock -> loc 6 (labelled)
// in sysEmtMat0Attr -> loc 10
// in sysEmtMat1Attr -> loc 11
// in sysEmtMat2Attr -> loc 12
// in sysInitRotateAttr -> loc 9
// in sysLocalPosAttr -> loc 5
// in sysLocalVecAttr -> loc 6
// in sysNormalAttr -> loc 2
// in sysPosAttr -> loc 0
// in sysRandomAttr -> loc 8
// in sysScaleAttr -> loc 7
// in sysTangentAttr -> loc 3
// in sysTexCoordAttr -> loc 1
// in sysVertexColor0Attr -> loc 4
#version 450 core
#extension GL_ARB_gpu_shader_int64 : enable
#extension GL_ARB_shader_ballot : enable
#extension GL_ARB_shader_group_vote : enable
#extension GL_EXT_shader_image_load_formatted : enable
#extension GL_EXT_texture_shadow_lod : enable
#extension GL_ARB_shader_draw_parameters : enable
#extension GL_ARB_shader_viewport_layer_array : enable
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

layout (binding = 10, std140) uniform _NnVfx2EmitterDynamicParam
{
    precise vec4 data[4096];
} NnVfx2EmitterDynamicParam;

layout (binding = 8, std140) uniform _NnVfx2ViewParam
{
    precise vec4 data[4096];
} NnVfx2ViewParam;

layout (binding = 9, std140) uniform _sysEmitterStaticUniformBlock
{
    precise vec4 data[4096];
} sysEmitterStaticUniformBlock;

layout (binding = 14, std140) uniform _sysCustomShaderUniformBlock0
{
    precise vec4 data[4096];
} sysCustomShaderUniformBlock0;

layout (binding = 1, std140) uniform _vp_c1
{
    precise vec4 data[4096];
} vp_c1;

layout (binding = 15, std140) uniform _sysCustomShaderUniformBlock1
{
    precise vec4 data[4096];
} sysCustomShaderUniformBlock1;

layout (binding = 0) uniform sampler2D sysCustomShaderTextureSampler2;
layout (binding = 1) uniform sampler2D sysCustomShaderTextureSampler1;
layout (binding = 2) uniform sampler2DShadow sysCustomShaderShadowSampler0;
layout (binding = 3) uniform sampler2DArrayShadow sysCustomShaderShadowArraySampler0;
layout (location = 0) in vec4 sysPosAttr;
layout (location = 1) in vec4 sysTexCoordAttr;
layout (location = 2) in vec4 sysNormalAttr;
layout (location = 3) in vec4 sysTangentAttr;
layout (location = 4) in vec4 sysVertexColor0Attr;
layout (location = 5) in vec4 sysLocalPosAttr;
layout (location = 6) in vec4 sysLocalVecAttr;
layout (location = 7) in vec4 sysScaleAttr;
layout (location = 8) in vec4 sysRandomAttr;
layout (location = 9) in vec4 sysInitRotateAttr;
layout (location = 10) in vec4 sysEmtMat0Attr;
layout (location = 11) in vec4 sysEmtMat1Attr;
layout (location = 12) in vec4 sysEmtMat2Attr;

layout (location = 0) out vec4 out_attr0;
layout (location = 1) out vec4 out_attr1;
layout (location = 2) out vec4 out_attr2;
layout (location = 3) out vec4 out_attr3;
layout (location = 4) out vec4 out_attr4;
layout (location = 5) out vec4 out_attr5;
layout (location = 6) out vec4 out_attr6;
layout (location = 7) out vec4 out_attr7;
layout (location = 8) out vec4 out_attr8;
layout (location = 9) out vec4 out_attr9;
layout (location = 10) out vec4 out_attr10;
layout (location = 11) out vec4 out_attr11;
layout (location = 12) out vec4 out_attr12;
layout (location = 13) out vec4 out_attr13;
layout (location = 14) out vec4 out_attr14;
layout (location = 15) out vec4 out_attr15;


void main()
{
    precise float temp_0;
    precise float temp_1;
    precise float temp_2;
    bool temp_3;
    precise float temp_4;
    precise float temp_5;
    int temp_6;
    precise float temp_7;
    precise float temp_8;
    precise float temp_9;
    bool temp_10;
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
    bool temp_43;
    bool temp_44;
    precise float temp_45;
    precise float temp_46;
    bool temp_47;
    precise float temp_48;
    precise float temp_49;
    precise float temp_50;
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
    precise float temp_109;
    precise float temp_110;
    precise float temp_111;
    precise float temp_112;
    precise float temp_113;
    precise float temp_114;
    precise float temp_115;
    precise float temp_116;
    precise float temp_117;
    precise float temp_118;
    bool temp_119;
    precise float temp_120;
    int temp_121;
    precise float temp_122;
    precise float temp_123;
    precise float temp_124;
    precise float temp_125;
    int temp_126;
    int temp_127;
    precise float temp_128;
    int temp_129;
    precise float temp_130;
    bool temp_131;
    bool temp_132;
    bool temp_133;
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
    precise vec2 temp_183;
    precise float temp_184;
    precise float temp_185;
    precise float temp_186;
    precise float temp_187;
    precise float temp_188;
    int temp_189;
    bool temp_190;
    int temp_191;
    precise float temp_192;
    precise float temp_193;
    bool temp_194;
    precise float temp_195;
    precise float temp_196;
    precise float temp_197;
    precise float temp_198;
    precise float temp_199;
    precise float temp_200;
    precise float temp_201;
    int temp_202;
    int temp_203;
    precise float temp_204;
    int temp_205;
    precise float temp_206;
    bool temp_207;
    precise float temp_208;
    int temp_209;
    int temp_210;
    int temp_211;
    uint temp_212;
    uint temp_213;
    bool temp_214;
    uint temp_215;
    uint temp_216;
    precise float temp_217;
    precise float temp_218;
    precise float temp_219;
    precise float temp_220;
    precise float temp_221;
    precise float temp_222;
    precise float temp_223;
    precise float temp_224;
    precise float temp_225;
    precise float temp_226;
    precise float temp_227;
    precise float temp_228;
    precise float temp_229;
    precise float temp_230;
    precise float temp_231;
    precise float temp_232;
    precise float temp_233;
    precise float temp_234;
    bool temp_235;
    precise float temp_236;
    precise float temp_237;
    precise float temp_238;
    precise float temp_239;
    precise float temp_240;
    precise float temp_241;
    int temp_242;
    int temp_243;
    int temp_244;
    precise float temp_245;
    precise float temp_246;
    int temp_247;
    precise float temp_248;
    precise float temp_249;
    precise float temp_250;
    precise float temp_251;
    precise float temp_252;
    precise float temp_253;
    precise float temp_254;
    precise float temp_255;
    precise float temp_256;
    int temp_257;
    int temp_258;
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
    precise float temp_276;
    precise float temp_277;
    bool temp_278;
    precise float temp_279;
    precise float temp_280;
    precise float temp_281;
    precise float temp_282;
    precise float temp_283;
    precise float temp_284;
    precise float temp_285;
    precise float temp_286;
    precise float temp_287;
    precise float temp_288;
    precise float temp_289;
    precise float temp_290;
    precise float temp_291;
    precise float temp_292;
    precise float temp_293;
    precise float temp_294;
    bool temp_295;
    precise float temp_296;
    precise float temp_297;
    precise float temp_298;
    precise float temp_299;
    precise float temp_300;
    precise float temp_301;
    precise float temp_302;
    precise float temp_303;
    precise float temp_304;
    precise float temp_305;
    precise float temp_306;
    precise float temp_307;
    precise float temp_308;
    precise float temp_309;
    gl_PointSize = 1.0;
    gl_Position.x = 0.0;
    gl_Position.y = 0.0;
    gl_Position.z = 0.0;
    gl_Position.w = 1.0;
    temp_0 = sysLocalVecAttr.w;
    temp_1 = (0.0 - temp_0) + NnVfx2EmitterDynamicParam.data[2].x;
    temp_2 = float(int(trunc(sysLocalPosAttr.w)));
    temp_3 = temp_0 > NnVfx2EmitterDynamicParam.data[2].x || temp_1 >= temp_2;
    temp_4 = temp_0;
    if (temp_3)
    {
        temp_4 = NnVfx2ViewParam.data[30].y;
    }
    temp_5 = temp_4;
    temp_6 = floatBitsToInt(temp_5);
    if (temp_3)
    {
        gl_Position.x = 0.0;
    }
    if (temp_3)
    {
        temp_6 = floatBitsToInt(temp_5 * 5.0);
    }
    if (temp_3)
    {
        gl_Position.y = 0.0;
    }
    if (temp_3)
    {
        gl_Position.z = intBitsToFloat(temp_6);
    }
    if (temp_3)
    {
        out_attr4.x = 0.0;
    }
    if (temp_3)
    {
        return;
    }
    temp_7 = sysEmtMat0Attr.x;
    temp_8 = temp_1 + NnVfx2EmitterDynamicParam.data[2].w;
    temp_9 = sysEmtMat1Attr.x;
    temp_10 = sysEmitterStaticUniformBlock.data[14].x == 1.0;
    temp_11 = sysEmtMat2Attr.x;
    temp_12 = sysEmtMat0Attr.y;
    temp_13 = sysEmtMat1Attr.y;
    temp_14 = sysEmtMat2Attr.y;
    temp_15 = intBitsToFloat(undef);
    temp_16 = temp_8;
    temp_17 = sysEmitterStaticUniformBlock.data[14].x;
    if (temp_10)
    {
        temp_15 = temp_8 * temp_8;
    }
    temp_18 = temp_15;
    temp_19 = sysEmtMat0Attr.z;
    temp_20 = sysEmtMat1Attr.z;
    temp_21 = sysEmtMat2Attr.z;
    temp_22 = sysRandomAttr.x;
    temp_23 = sysLocalVecAttr.y;
    temp_24 = fma(temp_19, temp_19, fma(temp_12, temp_12, temp_7 * temp_7));
    temp_25 = sysLocalPosAttr.x;
    temp_26 = fma(temp_20, temp_20, fma(temp_13, temp_13, temp_9 * temp_9));
    temp_27 = temp_18;
    temp_28 = sqrt(temp_24);
    temp_29 = temp_23;
    temp_30 = temp_24;
    temp_31 = temp_26;
    temp_32 = temp_25;
    if (temp_10)
    {
        temp_27 = temp_18 * sysEmitterStaticUniformBlock.data[13].w;
    }
    temp_33 = temp_27;
    temp_34 = fma(temp_21, temp_21, fma(temp_14, temp_14, temp_11 * temp_11));
    temp_35 = sysScaleAttr.w;
    temp_36 = intBitsToFloat(undef);
    temp_37 = temp_33;
    temp_38 = sqrt(temp_26);
    temp_39 = sqrt(temp_34);
    temp_40 = temp_34;
    if (temp_10)
    {
        temp_36 = temp_33 * 0.5 * sysEmitterStaticUniformBlock.data[13].y;
    }
    temp_41 = intBitsToFloat(undef);
    temp_42 = temp_36;
    if (temp_10)
    {
        temp_41 = temp_33 * 0.5 * sysEmitterStaticUniformBlock.data[13].z;
    }
    temp_43 = sqrt(temp_24) > 0.0;
    temp_44 = sqrt(temp_26) > 0.0;
    temp_45 = intBitsToFloat(undef);
    temp_46 = temp_41;
    if (temp_10)
    {
        temp_45 = temp_33 * 0.5 * sysEmitterStaticUniformBlock.data[13].x;
    }
    temp_47 = sqrt(temp_34) > 0.0;
    temp_48 = temp_45;
    if (!temp_10)
    {
        temp_49 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[14].x) + 1.0);
        temp_50 = 1.0 / log2(sysEmitterStaticUniformBlock.data[14].x);
        temp_51 = temp_50 * 1.44269502;
        temp_52 = (temp_8 + (0.0 - fma(temp_51, exp2(temp_8 * log2(abs(sysEmitterStaticUniformBlock.data[14].x))), (0.0 - temp_51)))) * temp_49 * sysEmitterStaticUniformBlock.data[13].w;
        temp_42 = temp_52 * sysEmitterStaticUniformBlock.data[13].y;
        temp_48 = temp_52 * sysEmitterStaticUniformBlock.data[13].x;
        temp_46 = temp_52 * sysEmitterStaticUniformBlock.data[13].z;
        temp_37 = temp_52;
        temp_38 = temp_50;
        temp_39 = temp_51;
        temp_28 = temp_49;
    }
    temp_53 = temp_38;
    temp_54 = temp_39;
    temp_55 = temp_37;
    temp_56 = temp_28;
    if (!temp_10)
    {
        temp_57 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[14].x) + 1.0);
        temp_58 = exp2(temp_8 * log2(abs(sysEmitterStaticUniformBlock.data[14].x)));
        temp_16 = fma(temp_58, (0.0 - temp_57), temp_57);
        temp_53 = temp_57;
        temp_54 = temp_58;
    }
    temp_59 = temp_16;
    temp_60 = temp_53;
    temp_61 = temp_54;
    temp_62 = temp_59;
    if (temp_43)
    {
        temp_55 = inversesqrt(temp_24);
    }
    temp_63 = temp_55;
    temp_64 = temp_63;
    if (temp_44)
    {
        temp_17 = inversesqrt(temp_26);
    }
    temp_65 = temp_17;
    if (temp_47)
    {
        temp_29 = inversesqrt(temp_34);
    }
    temp_66 = temp_29;
    if (!temp_43)
    {
        temp_60 = 0.0;
    }
    temp_67 = fma(fma(temp_59, temp_23, temp_42), temp_35, sysLocalPosAttr.y);
    temp_68 = temp_60;
    if (!temp_43)
    {
        temp_30 = 0.0;
    }
    temp_69 = fma(fma(temp_59, sysLocalVecAttr.x, temp_48), temp_35, temp_25);
    temp_70 = fma(fma(temp_59, sysLocalVecAttr.z, temp_46), temp_35, sysLocalPosAttr.z);
    temp_71 = temp_30;
    if (!temp_43)
    {
        temp_31 = 0.0;
    }
    temp_72 = temp_31;
    if (!temp_44)
    {
        temp_40 = 0.0;
    }
    temp_73 = temp_40;
    if (temp_43)
    {
        temp_71 = temp_63 * temp_7;
    }
    temp_74 = temp_71;
    if (temp_43)
    {
        temp_68 = temp_63 * temp_9;
    }
    temp_75 = temp_68;
    if (temp_43)
    {
        temp_72 = temp_63 * temp_11;
    }
    temp_76 = temp_72;
    if (temp_44)
    {
        temp_61 = temp_65 * temp_12;
    }
    temp_77 = temp_61;
    if (temp_44)
    {
        temp_62 = temp_65 * temp_13;
    }
    temp_78 = temp_62;
    if (temp_44)
    {
        temp_73 = temp_65 * temp_14;
    }
    temp_79 = temp_73;
    if (temp_47)
    {
        temp_64 = temp_66 * temp_19;
    }
    temp_80 = temp_64;
    if (temp_47)
    {
        temp_56 = temp_66 * temp_20;
    }
    temp_81 = temp_56;
    if (temp_47)
    {
        temp_32 = temp_66 * temp_21;
    }
    temp_82 = temp_32;
    if (!temp_44)
    {
        temp_78 = 0.0;
    }
    temp_83 = temp_78;
    if (!temp_44)
    {
        temp_77 = 0.0;
    }
    temp_84 = temp_77;
    if (!temp_47)
    {
        temp_82 = 0.0;
    }
    temp_85 = temp_82;
    if (!temp_47)
    {
        temp_81 = 0.0;
    }
    temp_86 = temp_81;
    if (!temp_47)
    {
        temp_80 = 0.0;
    }
    temp_87 = temp_80;
    if (0.0 < sysEmitterStaticUniformBlock.data[11].x)
    {
        temp_88 = fma(temp_22 * sysEmitterStaticUniformBlock.data[12].y, sysEmitterStaticUniformBlock.data[11].x, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[11].x);
        temp_89 = temp_88 + (0.0 - floor(temp_88));
    }
    else
    {
        temp_89 = temp_1 * (1.0 / temp_2);
    }
    temp_90 = temp_89;
    temp_91 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[140].w) + sysEmitterStaticUniformBlock.data[141].w);
    temp_92 = 1.0 / (sysEmitterStaticUniformBlock.data[142].w + (0.0 - sysEmitterStaticUniformBlock.data[141].w));
    temp_93 = temp_90 + (0.0 - sysEmitterStaticUniformBlock.data[141].w);
    temp_94 = temp_90 >= sysEmitterStaticUniformBlock.data[142].w ? 1.0 : 0.0;
    temp_95 = temp_90 >= sysEmitterStaticUniformBlock.data[140].w ? 1.0 : 0.0;
    temp_96 = temp_90 >= sysEmitterStaticUniformBlock.data[141].w ? 1.0 : 0.0;
    temp_97 = temp_90 + (0.0 - sysEmitterStaticUniformBlock.data[140].w);
    temp_98 = fma(temp_95, (0.0 - temp_96), temp_95);
    temp_99 = fma(temp_96, (0.0 - temp_94), temp_96);
    if (0.0 < sysEmitterStaticUniformBlock.data[10].x)
    {
        temp_100 = fma(temp_22 * sysEmitterStaticUniformBlock.data[11].y, sysEmitterStaticUniformBlock.data[10].x, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[10].x);
        temp_101 = temp_100 + (0.0 - floor(temp_100));
    }
    else
    {
        temp_101 = temp_1 * (1.0 / temp_2);
    }
    temp_102 = temp_101;
    temp_103 = temp_102 >= sysEmitterStaticUniformBlock.data[104].w ? 1.0 : 0.0;
    temp_104 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[104].w) + sysEmitterStaticUniformBlock.data[105].w);
    temp_105 = temp_102 + (0.0 - sysEmitterStaticUniformBlock.data[104].w);
    temp_106 = temp_102 >= sysEmitterStaticUniformBlock.data[105].w ? 1.0 : 0.0;
    temp_107 = fma(temp_103, (0.0 - temp_106), temp_103);
    if (0.0 < sysEmitterStaticUniformBlock.data[10].y)
    {
        temp_108 = fma(temp_22 * sysEmitterStaticUniformBlock.data[11].z, sysEmitterStaticUniformBlock.data[10].y, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[10].y);
        temp_109 = temp_108 + (0.0 - floor(temp_108));
    }
    else
    {
        temp_109 = temp_1 * (1.0 / temp_2);
    }
    temp_110 = temp_109;
    temp_111 = temp_110 >= sysEmitterStaticUniformBlock.data[112].w ? 1.0 : 0.0;
    temp_112 = temp_110 >= sysEmitterStaticUniformBlock.data[113].w ? 1.0 : 0.0;
    temp_113 = temp_110 >= sysEmitterStaticUniformBlock.data[114].w ? 1.0 : 0.0;
    out_attr0.x = fma(temp_106, sysEmitterStaticUniformBlock.data[105].x, fma(fma(temp_105, (sysEmitterStaticUniformBlock.data[105].x + (0.0 - sysEmitterStaticUniformBlock.data[104].x)) * temp_104, sysEmitterStaticUniformBlock.data[104].x), temp_107, fma(temp_103, (0.0 - sysEmitterStaticUniformBlock.data[104].x), sysEmitterStaticUniformBlock.data[104].x))) * NnVfx2EmitterDynamicParam.data[0].x * sysEmitterStaticUniformBlock.data[103].x;
    out_attr0.y = fma(temp_106, sysEmitterStaticUniformBlock.data[105].y, fma(fma(temp_105, (sysEmitterStaticUniformBlock.data[105].y + (0.0 - sysEmitterStaticUniformBlock.data[104].y)) * temp_104, sysEmitterStaticUniformBlock.data[104].y), temp_107, fma(temp_103, (0.0 - sysEmitterStaticUniformBlock.data[104].y), sysEmitterStaticUniformBlock.data[104].y))) * NnVfx2EmitterDynamicParam.data[0].y * sysEmitterStaticUniformBlock.data[103].x;
    out_attr0.z = fma(temp_106, sysEmitterStaticUniformBlock.data[105].z, fma(fma(temp_105, (sysEmitterStaticUniformBlock.data[105].z + (0.0 - sysEmitterStaticUniformBlock.data[104].z)) * temp_104, sysEmitterStaticUniformBlock.data[104].z), temp_107, fma(temp_103, (0.0 - sysEmitterStaticUniformBlock.data[104].z), sysEmitterStaticUniformBlock.data[104].z))) * NnVfx2EmitterDynamicParam.data[0].z * sysEmitterStaticUniformBlock.data[103].x;
    out_attr0.w = fma(temp_113, sysEmitterStaticUniformBlock.data[114].x, fma(fma(((0.0 - sysEmitterStaticUniformBlock.data[113].x) + sysEmitterStaticUniformBlock.data[114].x) * (1.0 / (sysEmitterStaticUniformBlock.data[114].w + (0.0 - sysEmitterStaticUniformBlock.data[113].w))), temp_110 + (0.0 - sysEmitterStaticUniformBlock.data[113].w), sysEmitterStaticUniformBlock.data[113].x), fma(temp_112, (0.0 - temp_113), temp_112), fma(fma((sysEmitterStaticUniformBlock.data[113].x + (0.0 - sysEmitterStaticUniformBlock.data[112].x)) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[112].w) + sysEmitterStaticUniformBlock.data[113].w)), temp_110 + (0.0 - sysEmitterStaticUniformBlock.data[112].w), sysEmitterStaticUniformBlock.data[112].x), fma(temp_112, (0.0 - temp_111), temp_111), fma(temp_111, (0.0 - sysEmitterStaticUniformBlock.data[112].x), sysEmitterStaticUniformBlock.data[112].x)))) * NnVfx2EmitterDynamicParam.data[0].w;
    if (0.0 < sysEmitterStaticUniformBlock.data[10].w)
    {
        temp_114 = fma(temp_22 * sysEmitterStaticUniformBlock.data[12].x, sysEmitterStaticUniformBlock.data[10].w, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[10].w);
        temp_115 = temp_114 + (0.0 - floor(temp_114));
    }
    else
    {
        temp_115 = temp_1 * (1.0 / temp_2);
    }
    temp_116 = temp_115;
    temp_117 = sysRandomAttr.z;
    temp_118 = sysRandomAttr.y;
    temp_119 = 0.0 == sysEmitterStaticUniformBlock.data[162].w;
    temp_120 = floor(temp_22 * 2.0);
    temp_121 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x10000000;
    temp_122 = sysInitRotateAttr.x;
    temp_123 = sysInitRotateAttr.y;
    temp_124 = sysInitRotateAttr.z;
    temp_125 = intBitsToFloat(undef);
    if (temp_119)
    {
        temp_125 = 1.0;
    }
    temp_126 = (0 - (temp_121 > 0 ? -1 : 0)) + (0 - temp_121 >= 0 ? 0 : 1);
    temp_127 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x20000000;
    temp_128 = floor(temp_117 * 2.0);
    temp_129 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x40000000;
    temp_130 = floor(temp_118 * 2.0);
    temp_131 = sysEmitterStaticUniformBlock.data[162].w == 1.0;
    temp_132 = temp_127 > 0;
    temp_133 = temp_129 > 0;
    temp_134 = intBitsToFloat((temp_132 ? -1 : 0));
    temp_135 = intBitsToFloat((temp_133 ? -1 : 0));
    temp_136 = intBitsToFloat(temp_126);
    temp_137 = temp_125;
    if (!temp_119)
    {
        temp_134 = log2(abs(sysEmitterStaticUniformBlock.data[162].w));
    }
    temp_138 = temp_134;
    temp_139 = temp_138;
    if (!temp_131)
    {
        temp_135 = (0.0 - sysEmitterStaticUniformBlock.data[162].w) + 1.0;
    }
    if (!temp_131)
    {
        temp_136 = 1.0 / temp_135;
    }
    if (!temp_119)
    {
        temp_139 = temp_1 * temp_138;
    }
    temp_140 = ((0.0 - temp_128 < 0.0 ? 1.0 : 0.0) + (temp_128 > 0.0 ? 1.0 : 0.0)) * float(abs(temp_126));
    temp_141 = ((0.0 - temp_120 < 0.0 ? 1.0 : 0.0) + (temp_120 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_132 ? -1 : 0)) + (0 - temp_127 >= 0 ? 0 : 1)));
    temp_142 = fma(temp_22 + temp_117, 0.5, -0.5);
    temp_143 = intBitsToFloat(undef);
    temp_144 = temp_142;
    if (!temp_119)
    {
        temp_143 = temp_139;
    }
    if (!temp_119)
    {
        temp_137 = exp2(temp_143);
    }
    temp_145 = fma(fma(temp_22 + temp_118, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].x, 2.0, sysEmitterStaticUniformBlock.data[162].x);
    temp_146 = ((0.0 - temp_130 < 0.0 ? 1.0 : 0.0) + (temp_130 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_133 ? -1 : 0)) + (0 - temp_129 >= 0 ? 0 : 1)));
    temp_147 = fma(fma(temp_118 + temp_117, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].y, 2.0, sysEmitterStaticUniformBlock.data[162].y);
    temp_148 = fma(temp_142 * sysEmitterStaticUniformBlock.data[163].z, 2.0, sysEmitterStaticUniformBlock.data[162].z);
    temp_149 = sysPosAttr.x;
    if (!temp_131)
    {
        temp_144 = fma(temp_136, (0.0 - temp_137), temp_136);
    }
    temp_150 = sysPosAttr.y;
    temp_151 = sysPosAttr.z;
    temp_152 = temp_144;
    if (temp_131)
    {
        temp_152 = temp_1;
    }
    temp_153 = temp_152;
    temp_154 = fma(fma(temp_145 * temp_140, -2.0, temp_145), temp_153, fma(temp_22 + -0.5, sysEmitterStaticUniformBlock.data[161].x, fma(temp_140 * temp_122, -2.0, temp_122)));
    temp_155 = fma(fma(temp_147 * temp_141, -2.0, temp_147), temp_153, fma(temp_118 + -0.5, sysEmitterStaticUniformBlock.data[161].y, fma(temp_141 * temp_123, -2.0, temp_123)));
    temp_156 = fma(fma(temp_148 * temp_146, -2.0, temp_148), temp_153, fma(temp_117 + -0.5, sysEmitterStaticUniformBlock.data[161].z, fma(temp_146 * temp_124, -2.0, temp_124)));
    temp_157 = (clamp(min(0.0, temp_22) + -0.0, 0.0, 1.0) + sysScaleAttr.x) * fma(temp_94, sysEmitterStaticUniformBlock.data[142].x, fma(fma((sysEmitterStaticUniformBlock.data[142].x + (0.0 - sysEmitterStaticUniformBlock.data[141].x)) * temp_92, temp_93, sysEmitterStaticUniformBlock.data[141].x), temp_99, fma(fma(temp_97, (sysEmitterStaticUniformBlock.data[141].x + (0.0 - sysEmitterStaticUniformBlock.data[140].x)) * temp_91, sysEmitterStaticUniformBlock.data[140].x), temp_98, fma(temp_95, (0.0 - sysEmitterStaticUniformBlock.data[140].x), sysEmitterStaticUniformBlock.data[140].x)))) * NnVfx2EmitterDynamicParam.data[3].y * fma(0.5, sysEmitterStaticUniformBlock.data[15].x, temp_149);
    temp_158 = fma(temp_94, sysEmitterStaticUniformBlock.data[142].y, fma(fma((sysEmitterStaticUniformBlock.data[142].y + (0.0 - sysEmitterStaticUniformBlock.data[141].y)) * temp_92, temp_93, sysEmitterStaticUniformBlock.data[141].y), temp_99, fma(fma(temp_97, (sysEmitterStaticUniformBlock.data[141].y + (0.0 - sysEmitterStaticUniformBlock.data[140].y)) * temp_91, sysEmitterStaticUniformBlock.data[140].y), temp_98, fma(temp_95, (0.0 - sysEmitterStaticUniformBlock.data[140].y), sysEmitterStaticUniformBlock.data[140].y)))) * sysScaleAttr.y * NnVfx2EmitterDynamicParam.data[3].z * fma(0.5, sysEmitterStaticUniformBlock.data[15].y, temp_150);
    temp_159 = fma(temp_94, sysEmitterStaticUniformBlock.data[142].z, fma(fma((sysEmitterStaticUniformBlock.data[142].z + (0.0 - sysEmitterStaticUniformBlock.data[141].z)) * temp_92, temp_93, sysEmitterStaticUniformBlock.data[141].z), temp_99, fma(fma(temp_97, (sysEmitterStaticUniformBlock.data[141].z + (0.0 - sysEmitterStaticUniformBlock.data[140].z)) * temp_91, sysEmitterStaticUniformBlock.data[140].z), temp_98, fma(temp_95, (0.0 - sysEmitterStaticUniformBlock.data[140].z), sysEmitterStaticUniformBlock.data[140].z)))) * sysScaleAttr.z * NnVfx2EmitterDynamicParam.data[3].w * fma(0.5, sysEmitterStaticUniformBlock.data[15].z, temp_151);
    temp_160 = cos(temp_155) * cos(temp_154);
    temp_161 = sin(temp_154) * cos(temp_155);
    temp_162 = cos(temp_155) * cos(temp_156);
    temp_163 = sin(temp_154) * sin(temp_155);
    temp_164 = cos(temp_154) * cos(temp_156);
    temp_165 = sin(temp_154) * cos(temp_156);
    temp_166 = sin(temp_155) * cos(temp_154);
    temp_167 = sin(temp_155) * cos(temp_156);
    temp_168 = fma(sin(temp_156), temp_160, temp_163);
    temp_169 = fma(sin(temp_156), temp_161, (0.0 - temp_166));
    temp_170 = fma(sin(temp_156), temp_166, (0.0 - temp_161));
    temp_171 = fma(sin(temp_156), temp_163, temp_160);
    temp_172 = 0.0 + fma(temp_159, temp_167, fma(temp_157, temp_162, sin(temp_156) * (0.0 - temp_158)));
    temp_173 = 0.0 + fma(temp_170, temp_159, fma(temp_168, temp_157, temp_158 * temp_164));
    temp_174 = fma(temp_70, temp_19, fma(temp_67, temp_12, temp_69 * temp_7)) + sysEmtMat0Attr.w;
    temp_175 = 0.0 + fma(temp_171, temp_159, fma(temp_169, temp_157, temp_158 * temp_165));
    temp_176 = fma(0.0, temp_159, fma(0.0, temp_157, 0.0 * temp_158)) + 1.0;
    temp_177 = fma(temp_70, temp_20, fma(temp_67, temp_13, temp_69 * temp_9)) + sysEmtMat1Attr.w;
    temp_178 = fma(temp_70, temp_21, fma(temp_67, temp_14, temp_69 * temp_11)) + sysEmtMat2Attr.w;
    temp_179 = fma(temp_174, temp_176, fma(temp_175, temp_87, fma(temp_173, temp_84, temp_172 * temp_74)));
    temp_180 = fma(temp_177, temp_176, fma(temp_175, temp_86, fma(temp_173, temp_83, temp_172 * temp_75)));
    temp_181 = fma(temp_178, temp_176, fma(temp_175, temp_85, fma(temp_173, temp_79, temp_172 * temp_76)));
    temp_182 = 1.0 / (fma(temp_181, sysCustomShaderUniformBlock0.data[5].z, fma(temp_180, sysCustomShaderUniformBlock0.data[5].y, temp_179 * sysCustomShaderUniformBlock0.data[5].x)) + sysCustomShaderUniformBlock0.data[5].w);
    temp_183 = texture(sysCustomShaderTextureSampler1, vec2((fma(temp_181, sysCustomShaderUniformBlock0.data[2].z, fma(temp_180, sysCustomShaderUniformBlock0.data[2].y, temp_179 * sysCustomShaderUniformBlock0.data[2].x)) + sysCustomShaderUniformBlock0.data[2].w) * temp_182, (fma(temp_181, sysCustomShaderUniformBlock0.data[3].z, fma(temp_180, sysCustomShaderUniformBlock0.data[3].y, temp_179 * sysCustomShaderUniformBlock0.data[3].x)) + sysCustomShaderUniformBlock0.data[3].w) * temp_182)).xy;
    temp_184 = temp_183.x;
    temp_185 = sysNormalAttr.x;
    temp_186 = sysNormalAttr.y;
    temp_187 = sysNormalAttr.z;
    temp_188 = sysTexCoordAttr.x;
    temp_189 = int(trunc(sysEmitterStaticUniformBlock.data[82].z));
    temp_190 = ((!((1 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 1) || !(temp_22 > 0.5) ? -1 : 0)) != 0;
    temp_191 = int(trunc(sysEmitterStaticUniformBlock.data[77].z));
    temp_192 = temp_116 >= sysEmitterStaticUniformBlock.data[128].w ? 1.0 : 0.0;
    temp_193 = temp_116 >= sysEmitterStaticUniformBlock.data[129].w ? 1.0 : 0.0;
    temp_194 = sysRandomAttr.w > 0.5;
    temp_195 = fma(temp_192, (0.0 - temp_193), temp_192);
    temp_196 = temp_188;
    temp_197 = temp_188;
    temp_198 = temp_195;
    temp_199 = temp_193;
    temp_200 = intBitsToFloat((temp_194 ? -1 : 0));
    if (!temp_190)
    {
        temp_196 = (0.0 - temp_188) + 1.0;
    }
    if (!(((!((4 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 4) || !(temp_117 > 0.5) ? -1 : 0)) != 0))
    {
        temp_197 = (0.0 - temp_188) + 1.0;
    }
    temp_201 = sysTexCoordAttr.y;
    temp_202 = floatBitsToInt(1.0 / float(uint(temp_189))) + -2;
    temp_203 = 0;
    temp_204 = temp_201;
    if ((1 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].z)) != 1)
    {
        temp_203 = 1;
    }
    temp_205 = temp_203;
    temp_206 = sysTangentAttr.y;
    temp_207 = temp_205 == 1;
    temp_208 = sysTangentAttr.z;
    temp_209 = floatBitsToInt(1.0 / float(uint(abs(temp_191)))) + -2;
    temp_210 = floatBitsToInt(1.0 / float(uint(temp_191))) + -2;
    temp_211 = floatBitsToInt(1.0 / float(uint(abs(temp_189)))) + -2;
    temp_212 = uint(max(trunc(float(0u) * intBitsToFloat(temp_202)), 0.0));
    temp_213 = uint(max(trunc(intBitsToFloat(temp_209) * float(0u)), 0.0));
    temp_214 = temp_151 == 0.0 && temp_149 == 0.0 && temp_150 == 0.0;
    temp_215 = uint(max(trunc(float(0u) * intBitsToFloat(temp_210)), 0.0));
    temp_216 = uint(max(trunc(float(0u) * intBitsToFloat(temp_211)), 0.0));
    temp_217 = temp_201;
    if (!(((!((2 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 2) || !(temp_118 > 0.5) ? -1 : 0)) != 0))
    {
        temp_217 = (0.0 - temp_201) + 1.0;
    }
    temp_218 = temp_22;
    temp_219 = temp_118;
    temp_220 = temp_22;
    temp_221 = temp_118;
    if (!(((!((8 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 8) || !temp_194 ? -1 : 0)) != 0))
    {
        temp_204 = (0.0 - temp_201) + 1.0;
    }
    if (temp_214)
    {
        temp_198 = temp_185;
    }
    temp_222 = temp_198;
    if (temp_214)
    {
        temp_199 = temp_186;
    }
    temp_223 = temp_199;
    if (temp_214)
    {
        temp_200 = temp_187;
    }
    temp_224 = temp_200;
    if (temp_207)
    {
        temp_218 = temp_118;
    }
    temp_225 = temp_218;
    temp_226 = temp_225;
    temp_227 = temp_225;
    if (temp_207)
    {
        temp_219 = temp_117;
    }
    temp_228 = temp_219;
    temp_229 = temp_228;
    temp_230 = temp_228;
    if (temp_207)
    {
        temp_220 = temp_118;
    }
    temp_231 = temp_220;
    temp_232 = temp_231;
    temp_233 = temp_231;
    if (temp_207)
    {
        temp_221 = temp_117;
    }
    temp_234 = temp_221;
    if (!temp_207)
    {
        temp_235 = temp_205 == 2;
        if (temp_235)
        {
            temp_226 = temp_117;
        }
        temp_227 = temp_226;
        if (temp_235)
        {
            temp_229 = temp_22;
        }
        temp_230 = temp_229;
        if (temp_235)
        {
            temp_232 = temp_22;
        }
        temp_233 = temp_232;
        if (temp_235)
        {
            temp_234 = temp_118;
        }
    }
    temp_236 = sysTangentAttr.x;
    out_attr12.x = temp_174;
    out_attr12.y = temp_177;
    out_attr12.z = temp_178;
    out_attr6.z = temp_181;
    if (!temp_214)
    {
        temp_222 = fma(temp_149, sysEmitterStaticUniformBlock.data[14].y, temp_185);
    }
    temp_237 = temp_222;
    out_attr6.x = temp_179;
    out_attr6.y = temp_180;
    temp_238 = sysTangentAttr.w;
    if (!temp_214)
    {
        temp_224 = fma(temp_151, sysEmitterStaticUniformBlock.data[14].y, temp_187);
    }
    temp_239 = temp_224;
    if (!temp_214)
    {
        temp_223 = fma(temp_150, sysEmitterStaticUniformBlock.data[14].y, temp_186);
    }
    temp_240 = temp_223;
    temp_241 = fma(temp_187, temp_236, (0.0 - temp_185 * temp_208)) * temp_238;
    temp_242 = int(temp_213) + int(uint(max(trunc(intBitsToFloat(temp_209) * float(uint((0 - abs(temp_191) * int(temp_213))))), 0.0)));
    temp_243 = int(temp_216) + int(uint(max(trunc(intBitsToFloat(temp_211) * float(uint((0 - abs(temp_189) * int(temp_216))))), 0.0)));
    temp_244 = int(temp_215) + int(uint(max(trunc(intBitsToFloat(temp_210) * float(uint((0 - temp_191 * int(temp_215))))), 0.0)));
    temp_245 = fma(temp_186, temp_208, (0.0 - temp_187 * temp_206)) * temp_238;
    temp_246 = fma(temp_185, temp_206, (0.0 - temp_186 * temp_236)) * temp_238;
    temp_247 = int(temp_212) + int(uint(max(trunc(intBitsToFloat(temp_202) * float(uint((0 - temp_189 * int(temp_212))))), 0.0)));
    temp_248 = 0.0 + fma(temp_167, temp_208, fma(temp_162, temp_236, sin(temp_156) * (0.0 - temp_206)));
    temp_249 = 0.0 + fma(temp_167, temp_239, fma(temp_162, temp_237, sin(temp_156) * (0.0 - temp_240)));
    temp_250 = 0.0 + fma(temp_167, temp_246, fma(temp_162, temp_245, sin(temp_156) * (0.0 - temp_241)));
    temp_251 = 0.0 + fma(temp_170, temp_208, fma(temp_168, temp_236, temp_164 * temp_206));
    temp_252 = 0.0 + fma(temp_170, temp_239, fma(temp_168, temp_237, temp_164 * temp_240));
    temp_253 = 0.0 + fma(temp_170, temp_246, fma(temp_168, temp_245, temp_164 * temp_241));
    temp_254 = 0.0 + fma(temp_171, temp_208, fma(temp_169, temp_236, temp_165 * temp_206));
    temp_255 = 0.0 + fma(temp_171, temp_239, fma(temp_169, temp_237, temp_165 * temp_240));
    temp_256 = 0.0 + fma(temp_171, temp_246, fma(temp_169, temp_245, temp_165 * temp_241));
    temp_257 = (0 - int(uint(temp_191) >> 31));
    temp_258 = (0 - int(uint(temp_189) >> 31));
    out_attr5.x = sysVertexColor0Attr.x;
    temp_259 = 1.0 / sysEmitterStaticUniformBlock.data[77].w * sysEmitterStaticUniformBlock.data[77].y;
    temp_260 = 1.0 / sysEmitterStaticUniformBlock.data[77].z * sysEmitterStaticUniformBlock.data[77].x;
    temp_261 = 1.0 / sysEmitterStaticUniformBlock.data[82].w * sysEmitterStaticUniformBlock.data[82].y;
    temp_262 = 1.0 / sysEmitterStaticUniformBlock.data[82].z * sysEmitterStaticUniformBlock.data[82].x;
    out_attr8.z = fma(0.0, temp_178, fma(temp_254, temp_85, fma(temp_251, temp_79, temp_248 * temp_76)));
    temp_263 = fma(temp_181, NnVfx2ViewParam.data[0].z, fma(temp_180, NnVfx2ViewParam.data[0].y, temp_179 * NnVfx2ViewParam.data[0].x)) + NnVfx2ViewParam.data[0].w;
    out_attr8.y = fma(0.0, temp_177, fma(temp_254, temp_86, fma(temp_251, temp_83, temp_248 * temp_75)));
    out_attr8.x = fma(0.0, temp_174, fma(temp_254, temp_87, fma(temp_251, temp_84, temp_248 * temp_74)));
    temp_264 = fma(temp_181, NnVfx2ViewParam.data[1].z, fma(temp_180, NnVfx2ViewParam.data[1].y, temp_179 * NnVfx2ViewParam.data[1].x)) + NnVfx2ViewParam.data[1].w;
    out_attr7.z = fma(0.0, temp_178, fma(temp_255, temp_85, fma(temp_252, temp_79, temp_249 * temp_76)));
    out_attr9.z = fma(0.0, temp_178, fma(temp_256, temp_85, fma(temp_253, temp_79, temp_250 * temp_76)));
    temp_265 = fma(temp_181, NnVfx2ViewParam.data[2].z, fma(temp_180, NnVfx2ViewParam.data[2].y, temp_179 * NnVfx2ViewParam.data[2].x)) + NnVfx2ViewParam.data[2].w;
    out_attr7.y = fma(0.0, temp_177, fma(temp_255, temp_86, fma(temp_252, temp_83, temp_249 * temp_75)));
    out_attr7.x = fma(0.0, temp_174, fma(temp_255, temp_87, fma(temp_252, temp_84, temp_249 * temp_74)));
    temp_266 = fma(temp_181, NnVfx2ViewParam.data[3].z, fma(temp_180, NnVfx2ViewParam.data[3].y, temp_179 * NnVfx2ViewParam.data[3].x)) + NnVfx2ViewParam.data[3].w;
    out_attr9.x = fma(0.0, temp_174, fma(temp_256, temp_87, fma(temp_253, temp_84, temp_250 * temp_74)));
    temp_267 = fma(temp_266, NnVfx2ViewParam.data[5].w, fma(temp_265, NnVfx2ViewParam.data[5].z, fma(temp_264, NnVfx2ViewParam.data[5].y, temp_263 * NnVfx2ViewParam.data[5].x)));
    gl_Position.y = temp_267;
    out_attr9.y = fma(0.0, temp_177, fma(temp_256, temp_86, fma(temp_253, temp_83, temp_250 * temp_75)));
    out_attr5.y = sysVertexColor0Attr.y;
    temp_268 = fma(temp_266, NnVfx2ViewParam.data[4].w, fma(temp_265, NnVfx2ViewParam.data[4].z, fma(temp_264, NnVfx2ViewParam.data[4].y, temp_263 * NnVfx2ViewParam.data[4].x)));
    out_attr5.z = sysVertexColor0Attr.z;
    gl_Position.x = temp_268;
    temp_269 = fma(temp_266, NnVfx2ViewParam.data[6].w, fma(temp_265, NnVfx2ViewParam.data[6].z, fma(temp_264, NnVfx2ViewParam.data[6].y, temp_263 * NnVfx2ViewParam.data[6].x)));
    temp_270 = fma(temp_266, NnVfx2ViewParam.data[7].w, fma(temp_265, NnVfx2ViewParam.data[7].z, fma(temp_264, NnVfx2ViewParam.data[7].y, temp_263 * NnVfx2ViewParam.data[7].x)));
    gl_Position.z = temp_269;
    gl_Position.w = temp_270;
    out_attr2.x = fma(fma(temp_260, temp_196, -0.5), fma(temp_1, sysEmitterStaticUniformBlock.data[74].z, fma(temp_22, sysEmitterStaticUniformBlock.data[75].z, sysEmitterStaticUniformBlock.data[75].x + sysEmitterStaticUniformBlock.data[75].z)), fma(temp_260, float(temp_191 < 0 || !(temp_191 == 0) ? (0 - temp_191 * (temp_244 + (0 - (uint((0 - temp_191 * temp_244)) >= uint(temp_191) ? -1 : 0)))) : -1), fma(temp_1, (0.0 - sysEmitterStaticUniformBlock.data[73].x), (0.0 - fma(temp_22 * sysEmitterStaticUniformBlock.data[74].x, -2.0, sysEmitterStaticUniformBlock.data[74].x + sysEmitterStaticUniformBlock.data[73].z))))) + 0.5;
    out_attr1.w = fma(temp_193, sysEmitterStaticUniformBlock.data[129].x, fma(fma((sysEmitterStaticUniformBlock.data[129].x + (0.0 - sysEmitterStaticUniformBlock.data[128].x)) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[128].w) + sysEmitterStaticUniformBlock.data[129].w)), temp_116 + (0.0 - sysEmitterStaticUniformBlock.data[128].w), sysEmitterStaticUniformBlock.data[128].x), temp_195, fma(temp_192, (0.0 - sysEmitterStaticUniformBlock.data[128].x), sysEmitterStaticUniformBlock.data[128].x))) * NnVfx2EmitterDynamicParam.data[1].w;
    temp_271 = 0.0 * temp_267;
    temp_272 = sysVertexColor0Attr.w;
    out_attr3.y = fma(temp_270, 0.5, fma(0.0, temp_269, fma(0.0, temp_268, temp_267 * -0.5)));
    temp_273 = clamp(fma(temp_181, sysCustomShaderUniformBlock0.data[4].z, fma(temp_180, sysCustomShaderUniformBlock0.data[4].y, temp_179 * sysCustomShaderUniformBlock0.data[4].x)) + sysCustomShaderUniformBlock0.data[4].w, 0.0, 1.0);
    out_attr2.z = fma(fma(temp_1, sysEmitterStaticUniformBlock.data[79].z, fma(temp_233, sysEmitterStaticUniformBlock.data[80].z, sysEmitterStaticUniformBlock.data[80].x + sysEmitterStaticUniformBlock.data[80].z)), fma(temp_262, temp_197, -0.5), fma(temp_262, float(temp_189 < 0 || !(temp_189 == 0) ? (0 - temp_189 * (temp_247 + (0 - (uint((0 - temp_189 * temp_247)) >= uint(temp_189) ? -1 : 0)))) : -1), fma(temp_1, (0.0 - sysEmitterStaticUniformBlock.data[78].x), (0.0 - fma(temp_227 * sysEmitterStaticUniformBlock.data[79].x, -2.0, sysEmitterStaticUniformBlock.data[79].x + sysEmitterStaticUniformBlock.data[78].z))))) + 0.5;
    temp_274 = fma(0.0, temp_268, temp_271);
    temp_275 = fma(temp_184, (0.0 - temp_184), temp_183.y);
    out_attr2.w = fma(fma(temp_1, sysEmitterStaticUniformBlock.data[79].w, fma(temp_234, sysEmitterStaticUniformBlock.data[80].w, sysEmitterStaticUniformBlock.data[80].w + sysEmitterStaticUniformBlock.data[80].y)), fma(temp_261, temp_204, -0.5), (0.0 - fma(temp_261, (0.0 - float(temp_189 < 0 || !(temp_189 == 0) ? (0 - temp_258) + (temp_243 + (0 - (uint((0 - abs(temp_189) * temp_243)) >= uint(abs(temp_189)) ? -1 : 0)) ^ temp_258) : -1)), fma(temp_1, sysEmitterStaticUniformBlock.data[78].y, fma(temp_230 * sysEmitterStaticUniformBlock.data[79].y, -2.0, sysEmitterStaticUniformBlock.data[79].y + sysEmitterStaticUniformBlock.data[78].w))))) + 0.5;
    out_attr2.y = fma(fma(temp_1, sysEmitterStaticUniformBlock.data[74].w, fma(temp_118, sysEmitterStaticUniformBlock.data[75].w, sysEmitterStaticUniformBlock.data[75].w + sysEmitterStaticUniformBlock.data[75].y)), fma(temp_259, temp_217, -0.5), (0.0 - fma(temp_259, (0.0 - float(temp_191 < 0 || !(temp_191 == 0) ? (0 - temp_257) + (temp_242 + (0 - (uint((0 - abs(temp_191) * temp_242)) >= uint(abs(temp_191)) ? -1 : 0)) ^ temp_257) : -1)), fma(temp_1, sysEmitterStaticUniformBlock.data[73].y, fma(temp_118 * sysEmitterStaticUniformBlock.data[74].y, -2.0, sysEmitterStaticUniformBlock.data[74].y + sysEmitterStaticUniformBlock.data[73].w))))) + 0.5;
    out_attr5.w = temp_272;
    temp_276 = temp_270 + fma(0.0, temp_269, temp_274);
    out_attr3.w = temp_276;
    temp_277 = fma(temp_270, 0.5, fma(temp_269, 0.5, temp_274));
    out_attr3.x = fma(temp_270, 0.5, fma(0.0, temp_269, fma(temp_268, 0.5, temp_271)));
    temp_278 = sysCustomShaderUniformBlock0.data[18].w <= 1.0;
    out_attr3.z = temp_277;
    out_attr4.x = NnVfx2EmitterDynamicParam.data[3].x;
    temp_279 = NnVfx2ViewParam.data[30].w;
    temp_280 = temp_272;
    if (temp_278)
    {
        temp_279 = 0.0;
    }
    temp_281 = temp_279;
    if (!temp_278)
    {
        temp_282 = 1.0 / fma(temp_277 * (1.0 / temp_276), NnVfx2ViewParam.data[30].w, (0.0 - NnVfx2ViewParam.data[30].y)) * (0.0 - NnVfx2ViewParam.data[30].z);
        if (sysCustomShaderUniformBlock0.data[18].w == 2.0)
        {
            temp_281 = float(abs((temp_282 > sysCustomShaderUniformBlock0.data[18].x ? -1 : 0)) + abs((temp_282 > sysCustomShaderUniformBlock0.data[18].y ? -1 : 0)));
        }
        else
        {
            temp_281 = float(abs((temp_282 > sysCustomShaderUniformBlock0.data[18].z ? -1 : 0)) + abs((temp_282 > sysCustomShaderUniformBlock0.data[18].x ? -1 : 0)) + abs((temp_282 > sysCustomShaderUniformBlock0.data[18].y ? -1 : 0)));
        }
    }
    temp_283 = temp_281;
    temp_284 = temp_283;
    if (temp_283 == 0.0)
    {
        temp_285 = fma(temp_181, sysCustomShaderUniformBlock0.data[9].z, fma(temp_180, sysCustomShaderUniformBlock0.data[9].y, temp_179 * sysCustomShaderUniformBlock0.data[9].x));
        temp_286 = temp_285 + sysCustomShaderUniformBlock0.data[9].w;
        temp_287 = fma(temp_181, sysCustomShaderUniformBlock0.data[8].z, fma(temp_180, sysCustomShaderUniformBlock0.data[8].y, temp_179 * sysCustomShaderUniformBlock0.data[8].x)) + sysCustomShaderUniformBlock0.data[8].w;
        temp_288 = fma(temp_181, sysCustomShaderUniformBlock0.data[6].z, fma(temp_180, sysCustomShaderUniformBlock0.data[6].y, temp_179 * sysCustomShaderUniformBlock0.data[6].x)) + sysCustomShaderUniformBlock0.data[6].w;
        temp_289 = fma(temp_181, sysCustomShaderUniformBlock0.data[7].z, fma(temp_180, sysCustomShaderUniformBlock0.data[7].y, temp_179 * sysCustomShaderUniformBlock0.data[7].x)) + sysCustomShaderUniformBlock0.data[7].w;
        temp_290 = temp_285;
    }
    else if (temp_283 == 1.0)
    {
        temp_291 = fma(temp_181, sysCustomShaderUniformBlock0.data[13].z, fma(temp_180, sysCustomShaderUniformBlock0.data[13].y, temp_179 * sysCustomShaderUniformBlock0.data[13].x));
        temp_286 = temp_291 + sysCustomShaderUniformBlock0.data[13].w;
        temp_287 = fma(temp_181, sysCustomShaderUniformBlock0.data[12].z, fma(temp_180, sysCustomShaderUniformBlock0.data[12].y, temp_179 * sysCustomShaderUniformBlock0.data[12].x)) + sysCustomShaderUniformBlock0.data[12].w;
        temp_288 = fma(temp_181, sysCustomShaderUniformBlock0.data[10].z, fma(temp_180, sysCustomShaderUniformBlock0.data[10].y, temp_179 * sysCustomShaderUniformBlock0.data[10].x)) + sysCustomShaderUniformBlock0.data[10].w;
        temp_289 = fma(temp_181, sysCustomShaderUniformBlock0.data[11].z, fma(temp_180, sysCustomShaderUniformBlock0.data[11].y, temp_179 * sysCustomShaderUniformBlock0.data[11].x)) + sysCustomShaderUniformBlock0.data[11].w;
        temp_290 = temp_291;
    }
    else
    {
        temp_292 = fma(temp_181, sysCustomShaderUniformBlock0.data[17].z, fma(temp_180, sysCustomShaderUniformBlock0.data[17].y, temp_179 * sysCustomShaderUniformBlock0.data[17].x));
        temp_286 = temp_292 + sysCustomShaderUniformBlock0.data[17].w;
        temp_287 = fma(temp_181, sysCustomShaderUniformBlock0.data[16].z, fma(temp_180, sysCustomShaderUniformBlock0.data[16].y, temp_179 * sysCustomShaderUniformBlock0.data[16].x)) + sysCustomShaderUniformBlock0.data[16].w;
        temp_288 = fma(temp_181, sysCustomShaderUniformBlock0.data[14].z, fma(temp_180, sysCustomShaderUniformBlock0.data[14].y, temp_179 * sysCustomShaderUniformBlock0.data[14].x)) + sysCustomShaderUniformBlock0.data[14].w;
        temp_289 = fma(temp_181, sysCustomShaderUniformBlock0.data[15].z, fma(temp_180, sysCustomShaderUniformBlock0.data[15].y, temp_179 * sysCustomShaderUniformBlock0.data[15].x)) + sysCustomShaderUniformBlock0.data[15].w;
        temp_290 = temp_292;
    }
    temp_293 = temp_286;
    temp_294 = temp_287;
    temp_295 = 0.0 == sysCustomShaderUniformBlock0.data[18].w;
    temp_296 = 1.0 / temp_293;
    temp_297 = temp_296 * temp_294;
    temp_298 = temp_296 * temp_288;
    temp_299 = temp_296 * temp_289;
    temp_300 = temp_290;
    temp_301 = temp_294;
    if (!temp_295)
    {
        temp_300 = temp_283;
    }
    temp_302 = temp_300;
    if (temp_295)
    {
        temp_302 = temp_297;
    }
    temp_303 = temp_302;
    if (temp_295)
    {
        temp_280 = texture(sysCustomShaderShadowSampler0, vec3(temp_298, temp_299, temp_303));
    }
    temp_304 = temp_280;
    if (!temp_295)
    {
        temp_301 = uintBitsToFloat(clamp(uint(max(roundEven(temp_303), 0.0)), 0u, 0xFFFFu));
    }
    if (temp_295)
    {
        temp_284 = temp_296 * temp_293;
    }
    temp_305 = temp_284;
    if (!temp_295)
    {
        temp_305 = temp_297;
    }
    if (!temp_295)
    {
        temp_304 = texture(sysCustomShaderShadowArraySampler0, vec4(temp_298, temp_299, float(floatBitsToInt(temp_301)), temp_305));
    }
    temp_306 = inversesqrt(fma(temp_265, temp_265, fma(temp_264, temp_264, temp_263 * temp_263)));
    out_attr15.x = temp_263 * temp_306;
    out_attr15.y = temp_264 * temp_306;
    if (0.0 < sysCustomShaderUniformBlock1.data[4].w)
    {
        temp_307 = (0.0 - temp_174) + temp_179;
        temp_308 = (0.0 - temp_177) + temp_180;
        temp_309 = (0.0 - temp_178) + temp_181;
        out_attr14.x = fma(fma(temp_309, NnVfx2ViewParam.data[0].z, fma(temp_308, NnVfx2ViewParam.data[0].y, temp_307 * NnVfx2ViewParam.data[0].x)), sysCustomShaderUniformBlock0.data[31].x, 0.5) * sysCustomShaderUniformBlock0.data[41].x;
        out_attr14.y = fma(fma(temp_309, NnVfx2ViewParam.data[1].z, fma(temp_308, NnVfx2ViewParam.data[1].y, temp_307 * NnVfx2ViewParam.data[1].x)), (0.0 - sysCustomShaderUniformBlock0.data[31].y), 0.5) * sysCustomShaderUniformBlock0.data[41].x;
    }
    out_attr15.z = temp_265 * temp_306;
    out_attr10.x = (0.0 - fma(temp_181, sysCustomShaderUniformBlock0.data[38].z, fma(temp_180, sysCustomShaderUniformBlock0.data[38].y, temp_179 * sysCustomShaderUniformBlock0.data[38].x))) + -0.0;
    out_attr11.x = sysCustomShaderUniformBlock0.data[36].w;
    out_attr13.x = clamp(0.0 + (0.0 - fma(texture(sysCustomShaderTextureSampler2, vec2(fma(temp_181, sysCustomShaderUniformBlock0.data[19].z, fma(temp_180, sysCustomShaderUniformBlock0.data[19].y, temp_179 * sysCustomShaderUniformBlock0.data[19].x)) + sysCustomShaderUniformBlock0.data[19].w, fma(temp_181, sysCustomShaderUniformBlock0.data[20].z, fma(temp_180, sysCustomShaderUniformBlock0.data[20].y, temp_179 * sysCustomShaderUniformBlock0.data[20].x)) + sysCustomShaderUniformBlock0.data[20].w)).x, (0.0 - sysCustomShaderUniformBlock0.data[22].x), sysCustomShaderUniformBlock0.data[22].x) + (0.0 - max(min(temp_275 * (1.0 / fma(temp_273 + (0.0 - temp_184), temp_273 + (0.0 - temp_184), temp_275)), 1.0), temp_273 <= temp_184 ? 1.0 : 0.0)) + 1.0 + (0.0 - temp_304)), 0.0, 1.0);
    return;
}
