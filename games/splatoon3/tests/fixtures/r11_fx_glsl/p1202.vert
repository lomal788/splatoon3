// static_grsn.bfsha model VfxGeneralShader program 1202 (vert)
// sampler sysTextureSampler0 -> loc 0 -> material sampler ?
// ubo NnVfx2EmitterDynamicParam -> loc 7 (labelled)
// ubo NnVfx2ViewParam -> loc 5 (labelled)
// ubo sysCustomShaderUniformBlock0 -> loc 11
// ubo sysCustomShaderUniformBlock1 -> loc 12
// ubo sysEmitterStaticUniformBlock -> loc 6 (labelled)
// in sysEmtMat0Attr -> loc 8
// in sysEmtMat1Attr -> loc 9
// in sysEmtMat2Attr -> loc 10
// in sysInitRotateAttr -> loc 7
// in sysLocalPosAttr -> loc 3
// in sysLocalVecAttr -> loc 4
// in sysNormalAttr -> loc 2
// in sysPosAttr -> loc 0
// in sysRandomAttr -> loc 6
// in sysScaleAttr -> loc 5
// in sysTexCoordAttr -> loc 1
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

layout (binding = 1, std140) uniform _vp_c1
{
    precise vec4 data[4096];
} vp_c1;

layout (binding = 14, std140) uniform _sysCustomShaderUniformBlock0
{
    precise vec4 data[4096];
} sysCustomShaderUniformBlock0;

layout (binding = 15, std140) uniform _sysCustomShaderUniformBlock1
{
    precise vec4 data[4096];
} sysCustomShaderUniformBlock1;

layout (binding = 0) uniform sampler2D sysTextureSampler0;
layout (location = 0) in vec4 sysPosAttr;
layout (location = 1) in vec4 sysTexCoordAttr;
layout (location = 2) in vec4 sysNormalAttr;
layout (location = 3) in vec4 sysLocalPosAttr;
layout (location = 4) in vec4 sysLocalVecAttr;
layout (location = 5) in vec4 sysScaleAttr;
layout (location = 6) in vec4 sysRandomAttr;
layout (location = 7) in vec4 sysInitRotateAttr;
layout (location = 8) in vec4 sysEmtMat0Attr;
layout (location = 9) in vec4 sysEmtMat1Attr;
layout (location = 10) in vec4 sysEmtMat2Attr;

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
    bool temp_8;
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
    bool temp_20;
    precise float temp_21;
    bool temp_22;
    precise float temp_23;
    precise float temp_24;
    precise float temp_25;
    precise float temp_26;
    precise float temp_27;
    bool temp_28;
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
    int temp_109;
    int temp_110;
    uint temp_111;
    int temp_112;
    uint temp_113;
    precise float temp_114;
    int temp_115;
    int temp_116;
    precise float temp_117;
    int temp_118;
    precise float temp_119;
    bool temp_120;
    precise float temp_121;
    precise float temp_122;
    precise float temp_123;
    precise float temp_124;
    precise float temp_125;
    precise float temp_126;
    precise float temp_127;
    precise float temp_128;
    bool temp_129;
    int temp_130;
    bool temp_131;
    int temp_132;
    int temp_133;
    precise float temp_134;
    bool temp_135;
    precise float temp_136;
    bool temp_137;
    precise float temp_138;
    precise float temp_139;
    bool temp_140;
    bool temp_141;
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
    bool temp_152;
    precise float temp_153;
    int temp_154;
    precise float temp_155;
    int temp_156;
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
    int temp_171;
    precise float temp_172;
    int temp_173;
    int temp_174;
    int temp_175;
    precise float temp_176;
    precise float temp_177;
    uint temp_178;
    precise float temp_179;
    uint temp_180;
    bool temp_181;
    precise float temp_182;
    int temp_183;
    precise float temp_184;
    precise float temp_185;
    precise float temp_186;
    precise float temp_187;
    precise float temp_188;
    precise float temp_189;
    precise float temp_190;
    precise float temp_191;
    precise float temp_192;
    precise float temp_193;
    precise float temp_194;
    precise float temp_195;
    precise float temp_196;
    precise float temp_197;
    precise float temp_198;
    precise float temp_199;
    bool temp_200;
    int temp_201;
    uint temp_202;
    uint temp_203;
    precise float temp_204;
    int temp_205;
    int temp_206;
    bool temp_207;
    precise float temp_208;
    precise float temp_209;
    precise float temp_210;
    precise float temp_211;
    precise float temp_212;
    precise float temp_213;
    precise float temp_214;
    precise float temp_215;
    precise float temp_216;
    precise float temp_217;
    precise float temp_218;
    precise float temp_219;
    precise float temp_220;
    precise float temp_221;
    bool temp_222;
    precise float temp_223;
    precise float temp_224;
    int temp_225;
    int temp_226;
    int temp_227;
    precise float temp_228;
    precise float temp_229;
    int temp_230;
    precise float temp_231;
    precise float temp_232;
    int temp_233;
    precise float temp_234;
    int temp_235;
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
    bool temp_269;
    precise float temp_270;
    precise float temp_271;
    precise float temp_272;
    precise float temp_273;
    precise float temp_274;
    precise float temp_275;
    precise float temp_276;
    precise float temp_277;
    precise float temp_278;
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
    precise float temp_295;
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
    precise float temp_310;
    precise float temp_311;
    precise float temp_312;
    precise float temp_313;
    precise float temp_314;
    precise float temp_315;
    precise float temp_316;
    precise float temp_317;
    precise float temp_318;
    precise float temp_319;
    precise float temp_320;
    precise float temp_321;
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
        out_attr3.x = 0.0;
    }
    if (temp_3)
    {
        return;
    }
    temp_7 = sysEmtMat0Attr.x;
    temp_8 = sysEmitterStaticUniformBlock.data[14].x == 1.0;
    temp_9 = sysEmtMat0Attr.y;
    temp_10 = sysEmtMat1Attr.x;
    temp_11 = sysEmtMat2Attr.x;
    temp_12 = sysEmtMat0Attr.z;
    temp_13 = sysEmtMat1Attr.y;
    temp_14 = sysEmtMat2Attr.y;
    temp_15 = sysEmtMat1Attr.z;
    temp_16 = sysEmtMat2Attr.z;
    temp_17 = fma(temp_12, temp_12, fma(temp_9, temp_9, temp_7 * temp_7));
    temp_18 = sysScaleAttr.w;
    temp_19 = fma(temp_15, temp_15, fma(temp_13, temp_13, temp_10 * temp_10));
    temp_20 = sqrt(temp_17) > 0.0;
    temp_21 = fma(temp_16, temp_16, fma(temp_14, temp_14, temp_11 * temp_11));
    temp_22 = sqrt(temp_19) > 0.0;
    temp_23 = intBitsToFloat(undef);
    temp_24 = sqrt(temp_21);
    temp_25 = sqrt(temp_17);
    if (temp_20)
    {
        temp_23 = inversesqrt(temp_17);
    }
    temp_26 = temp_23;
    temp_27 = temp_1 + NnVfx2EmitterDynamicParam.data[2].w;
    temp_28 = sqrt(temp_21) > 0.0;
    if (temp_8)
    {
        temp_24 = temp_27 * temp_27;
    }
    temp_29 = temp_24;
    temp_30 = temp_29;
    if (temp_22)
    {
        temp_25 = inversesqrt(temp_19);
    }
    temp_31 = temp_25;
    temp_32 = temp_31;
    if (temp_8)
    {
        temp_30 = temp_29 * sysEmitterStaticUniformBlock.data[13].w;
    }
    temp_33 = temp_30;
    temp_34 = intBitsToFloat(undef);
    temp_35 = temp_33;
    if (temp_28)
    {
        temp_34 = inversesqrt(temp_21);
    }
    temp_36 = temp_34;
    temp_37 = intBitsToFloat(undef);
    if (temp_8)
    {
        temp_37 = temp_33 * 0.5 * sysEmitterStaticUniformBlock.data[13].y;
    }
    temp_38 = intBitsToFloat(undef);
    temp_39 = temp_37;
    if (temp_8)
    {
        temp_38 = temp_33 * 0.5 * sysEmitterStaticUniformBlock.data[13].z;
    }
    temp_40 = intBitsToFloat(undef);
    temp_41 = temp_38;
    if (temp_8)
    {
        temp_40 = temp_33 * 0.5 * sysEmitterStaticUniformBlock.data[13].x;
    }
    temp_42 = temp_40;
    temp_43 = intBitsToFloat(undef);
    if (!temp_8)
    {
        temp_44 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[14].x) + 1.0);
        temp_45 = temp_27 * log2(abs(sysEmitterStaticUniformBlock.data[14].x));
        temp_46 = 1.0 / log2(sysEmitterStaticUniformBlock.data[14].x) * 1.44269502;
        temp_47 = (temp_27 + (0.0 - fma(temp_46, exp2(temp_45), (0.0 - temp_46)))) * temp_44 * sysEmitterStaticUniformBlock.data[13].w;
        temp_39 = temp_47 * sysEmitterStaticUniformBlock.data[13].y;
        temp_42 = temp_47 * sysEmitterStaticUniformBlock.data[13].x;
        temp_41 = temp_47 * sysEmitterStaticUniformBlock.data[13].z;
        temp_43 = temp_45;
        temp_35 = temp_44;
    }
    temp_48 = temp_39;
    temp_49 = temp_42;
    temp_50 = temp_41;
    temp_51 = intBitsToFloat(undef);
    temp_52 = temp_43;
    temp_53 = temp_35;
    if (temp_22)
    {
        temp_51 = temp_31 * temp_13;
    }
    temp_54 = sysRandomAttr.x;
    temp_55 = intBitsToFloat(undef);
    temp_56 = temp_51;
    if (temp_20)
    {
        temp_55 = temp_26 * temp_10;
    }
    temp_57 = temp_55;
    if (!temp_22)
    {
        temp_56 = 0.0;
    }
    temp_58 = temp_56;
    if (!temp_20)
    {
        temp_57 = 0.0;
    }
    temp_59 = temp_57;
    temp_60 = intBitsToFloat(undef);
    if (temp_28)
    {
        temp_60 = temp_36 * temp_15;
    }
    temp_61 = temp_60;
    if (!temp_28)
    {
        temp_61 = 0.0;
    }
    temp_62 = temp_61;
    temp_63 = intBitsToFloat(undef);
    if (temp_20)
    {
        temp_63 = temp_26 * temp_7;
    }
    temp_64 = intBitsToFloat(undef);
    temp_65 = temp_63;
    if (temp_22)
    {
        temp_64 = temp_31 * temp_9;
    }
    temp_66 = temp_64;
    if (!temp_20)
    {
        temp_65 = 0.0;
    }
    temp_67 = temp_65;
    if (!temp_22)
    {
        temp_66 = 0.0;
    }
    temp_68 = temp_66;
    temp_69 = intBitsToFloat(undef);
    if (temp_28)
    {
        temp_69 = temp_36 * temp_12;
    }
    temp_70 = temp_69;
    if (!temp_28)
    {
        temp_70 = 0.0;
    }
    temp_71 = temp_70;
    if (temp_22)
    {
        temp_52 = temp_31 * temp_14;
    }
    temp_72 = temp_52;
    if (temp_20)
    {
        temp_32 = temp_26 * temp_11;
    }
    temp_73 = fma(temp_49, temp_67, temp_48 * temp_59);
    temp_74 = temp_32;
    temp_75 = temp_73;
    if (!temp_22)
    {
        temp_72 = 0.0;
    }
    temp_76 = temp_72;
    if (!temp_20)
    {
        temp_74 = 0.0;
    }
    temp_77 = temp_74;
    if (temp_28)
    {
        temp_53 = temp_36 * temp_16;
    }
    temp_78 = temp_53;
    if (!temp_28)
    {
        temp_78 = 0.0;
    }
    temp_79 = temp_78;
    if (temp_8)
    {
        temp_75 = temp_27;
    }
    temp_80 = temp_75;
    if (!temp_8)
    {
        temp_81 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[14].x) + 1.0);
        temp_80 = fma(exp2(temp_27 * log2(abs(sysEmitterStaticUniformBlock.data[14].x))), (0.0 - temp_81), temp_81);
    }
    temp_82 = temp_80;
    temp_83 = fma(fma(temp_82, sysLocalVecAttr.x, fma(temp_50, temp_77, temp_73)), temp_18, sysLocalPosAttr.x);
    temp_84 = fma(fma(temp_82, sysLocalVecAttr.y, fma(temp_50, temp_76, fma(temp_49, temp_68, temp_48 * temp_58))), temp_18, sysLocalPosAttr.y);
    temp_85 = fma(fma(temp_82, sysLocalVecAttr.z, fma(temp_50, temp_79, fma(temp_49, temp_71, temp_48 * temp_62))), temp_18, sysLocalPosAttr.z);
    if (0.0 < sysEmitterStaticUniformBlock.data[11].x)
    {
        temp_86 = fma(temp_54 * sysEmitterStaticUniformBlock.data[12].y, sysEmitterStaticUniformBlock.data[11].x, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[11].x);
        temp_87 = temp_86 + (0.0 - floor(temp_86));
    }
    else
    {
        temp_87 = temp_1 * (1.0 / temp_2);
    }
    temp_88 = temp_87;
    temp_89 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[140].w) + sysEmitterStaticUniformBlock.data[141].w);
    temp_90 = 1.0 / (sysEmitterStaticUniformBlock.data[142].w + (0.0 - sysEmitterStaticUniformBlock.data[141].w));
    temp_91 = temp_88 + (0.0 - sysEmitterStaticUniformBlock.data[141].w);
    temp_92 = temp_88 >= sysEmitterStaticUniformBlock.data[140].w ? 1.0 : 0.0;
    temp_93 = temp_88 + (0.0 - sysEmitterStaticUniformBlock.data[140].w);
    temp_94 = temp_88 >= sysEmitterStaticUniformBlock.data[141].w ? 1.0 : 0.0;
    temp_95 = temp_88 >= sysEmitterStaticUniformBlock.data[142].w ? 1.0 : 0.0;
    temp_96 = fma(temp_92, (0.0 - temp_94), temp_92);
    temp_97 = fma(temp_94, (0.0 - temp_95), temp_94);
    if (0.0 < sysEmitterStaticUniformBlock.data[10].x)
    {
        temp_98 = fma(temp_54 * sysEmitterStaticUniformBlock.data[11].y, sysEmitterStaticUniformBlock.data[10].x, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[10].x);
        temp_99 = temp_98 + (0.0 - floor(temp_98));
    }
    else
    {
        temp_99 = temp_1 * (1.0 / temp_2);
    }
    temp_100 = temp_99;
    temp_101 = temp_100 >= sysEmitterStaticUniformBlock.data[104].w ? 1.0 : 0.0;
    temp_102 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[104].w) + sysEmitterStaticUniformBlock.data[105].w);
    temp_103 = temp_100 + (0.0 - sysEmitterStaticUniformBlock.data[104].w);
    temp_104 = temp_100 >= sysEmitterStaticUniformBlock.data[105].w ? 1.0 : 0.0;
    temp_105 = fma(temp_101, (0.0 - temp_104), temp_101);
    if (0.0 < sysEmitterStaticUniformBlock.data[10].y)
    {
        temp_106 = fma(temp_54 * sysEmitterStaticUniformBlock.data[11].z, sysEmitterStaticUniformBlock.data[10].y, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[10].y);
        temp_107 = temp_106 + (0.0 - floor(temp_106));
    }
    else
    {
        temp_107 = temp_1 * (1.0 / temp_2);
    }
    temp_108 = temp_107;
    temp_109 = int(trunc(sysEmitterStaticUniformBlock.data[77].z));
    temp_110 = floatBitsToInt(1.0 / float(uint(temp_109))) + -2;
    temp_111 = uint(max(trunc(float(0u) * intBitsToFloat(temp_110)), 0.0));
    temp_112 = floatBitsToInt(1.0 / float(uint(abs(temp_109)))) + -2;
    temp_113 = uint(max(trunc(intBitsToFloat(temp_112) * float(0u)), 0.0));
    temp_114 = sysRandomAttr.y;
    temp_115 = int(temp_111) + int(uint(max(trunc(intBitsToFloat(temp_110) * float(uint((0 - temp_109 * int(temp_111))))), 0.0)));
    temp_116 = int(temp_113) + int(uint(max(trunc(intBitsToFloat(temp_112) * float(uint((0 - abs(temp_109) * int(temp_113))))), 0.0)));
    temp_117 = sysTexCoordAttr.y;
    temp_118 = (0 - int(uint(temp_109) >> 31));
    temp_119 = sysTexCoordAttr.x;
    temp_120 = ((!((1 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 1) || !(temp_54 > 0.5) ? -1 : 0)) != 0;
    temp_121 = 1.0 / sysEmitterStaticUniformBlock.data[77].w * sysEmitterStaticUniformBlock.data[77].y;
    temp_122 = temp_119;
    temp_123 = 1.0 / sysEmitterStaticUniformBlock.data[77].z * sysEmitterStaticUniformBlock.data[77].x;
    temp_124 = temp_117;
    if (!temp_120)
    {
        temp_122 = (0.0 - temp_119) + 1.0;
    }
    if (!(((!((2 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 2) || !(temp_114 > 0.5) ? -1 : 0)) != 0))
    {
        temp_124 = (0.0 - temp_117) + 1.0;
    }
    temp_125 = textureLod(sysTextureSampler0, vec2(fma(fma(temp_123, temp_122, -0.5), fma(temp_1, sysEmitterStaticUniformBlock.data[74].z, fma(temp_54, sysEmitterStaticUniformBlock.data[75].z, sysEmitterStaticUniformBlock.data[75].x + sysEmitterStaticUniformBlock.data[75].z)), fma(temp_123, float(temp_109 < 0 || !(temp_109 == 0) ? (0 - temp_109 * (temp_115 + (0 - (uint((0 - temp_109 * temp_115)) >= uint(temp_109) ? -1 : 0)))) : -1), fma(temp_1, (0.0 - sysEmitterStaticUniformBlock.data[73].x), (0.0 - fma(temp_54 * sysEmitterStaticUniformBlock.data[74].x, -2.0, sysEmitterStaticUniformBlock.data[74].x + sysEmitterStaticUniformBlock.data[73].z))))) + 0.5, fma(fma(temp_1, sysEmitterStaticUniformBlock.data[74].w, fma(temp_114, sysEmitterStaticUniformBlock.data[75].w, sysEmitterStaticUniformBlock.data[75].w + sysEmitterStaticUniformBlock.data[75].y)), fma(temp_121, temp_124, -0.5), (0.0 - fma(temp_121, (0.0 - float(temp_109 < 0 || !(temp_109 == 0) ? (0 - temp_118) + (temp_116 + (0 - (uint((0 - abs(temp_109) * temp_116)) >= uint(abs(temp_109)) ? -1 : 0)) ^ temp_118) : -1)), fma(temp_1, sysEmitterStaticUniformBlock.data[73].y, fma(temp_114 * sysEmitterStaticUniformBlock.data[74].y, -2.0, sysEmitterStaticUniformBlock.data[74].y + sysEmitterStaticUniformBlock.data[73].w))))) + 0.5), 0.0).w;
    temp_126 = sysRandomAttr.z;
    temp_127 = sysInitRotateAttr.x;
    temp_128 = sysInitRotateAttr.z;
    temp_129 = (1 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].z)) != 1;
    temp_130 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x10000000;
    temp_131 = (16 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 16;
    temp_132 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x20000000;
    temp_133 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x40000000;
    temp_134 = floor(temp_54 * 2.0);
    temp_135 = (8 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 8;
    temp_136 = temp_1 * (1.0 / temp_2);
    temp_137 = ((!((4 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 4) || !(temp_126 > 0.5) ? -1 : 0)) != 0;
    temp_138 = floor(temp_126 * 2.0);
    temp_139 = fma(temp_85, temp_12, fma(temp_84, temp_9, temp_83 * temp_7)) + sysEmtMat0Attr.w;
    temp_140 = 0.0 == sysEmitterStaticUniformBlock.data[162].w;
    temp_141 = ((!temp_131 || !(temp_114 > 0.5) ? -1 : 0)) != 0;
    temp_142 = intBitsToFloat((temp_135 ? -1 : 0));
    temp_143 = intBitsToFloat((temp_131 ? -1 : 0));
    if (!temp_140)
    {
        temp_142 = log2(abs(sysEmitterStaticUniformBlock.data[162].w));
    }
    temp_144 = temp_136 >= sysEmitterStaticUniformBlock.data[148].w ? 1.0 : 0.0;
    temp_145 = temp_136 >= sysEmitterStaticUniformBlock.data[149].w ? 1.0 : 0.0;
    temp_146 = floor(temp_114 * 2.0);
    temp_147 = fma(temp_85, temp_16, fma(temp_84, temp_14, temp_83 * temp_11)) + sysEmtMat2Attr.w;
    temp_148 = fma(temp_85, temp_15, fma(temp_84, temp_13, temp_83 * temp_10)) + sysEmtMat1Attr.w;
    temp_149 = temp_119;
    temp_150 = temp_119;
    temp_151 = temp_146;
    if (!temp_137)
    {
        temp_149 = (0.0 - temp_119) + 1.0;
    }
    if (!temp_141)
    {
        temp_150 = (0.0 - temp_119) + 1.0;
    }
    if (!temp_140)
    {
        temp_143 = temp_1 * temp_142;
    }
    temp_152 = sysEmitterStaticUniformBlock.data[162].w == 1.0;
    temp_153 = temp_108 >= sysEmitterStaticUniformBlock.data[112].w ? 1.0 : 0.0;
    temp_154 = int(trunc(sysEmitterStaticUniformBlock.data[82].z));
    temp_155 = temp_108 >= sysEmitterStaticUniformBlock.data[113].w ? 1.0 : 0.0;
    temp_156 = int(trunc(sysEmitterStaticUniformBlock.data[87].z));
    temp_157 = intBitsToFloat(undef);
    if (!temp_140)
    {
        temp_157 = temp_143;
    }
    if (!temp_152)
    {
        temp_151 = (0.0 - sysEmitterStaticUniformBlock.data[162].w) + 1.0;
    }
    temp_158 = temp_151;
    temp_159 = intBitsToFloat(undef);
    temp_160 = temp_158;
    if (!temp_140)
    {
        temp_159 = exp2(temp_157);
    }
    temp_161 = temp_159;
    if (!temp_152)
    {
        temp_160 = 1.0 / temp_158;
    }
    temp_162 = fma(temp_54 + temp_126, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].z;
    temp_163 = temp_162;
    if (temp_140)
    {
        temp_161 = 1.0;
    }
    temp_164 = temp_136 >= sysEmitterStaticUniformBlock.data[150].w ? 1.0 : 0.0;
    temp_165 = fma(fma(temp_114 + temp_126, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].y, 2.0, sysEmitterStaticUniformBlock.data[162].y);
    temp_166 = fma(temp_162, 2.0, sysEmitterStaticUniformBlock.data[162].z);
    if (!temp_152)
    {
        temp_163 = fma(temp_160, (0.0 - temp_161), temp_160);
    }
    temp_167 = temp_163;
    temp_168 = temp_117;
    temp_169 = temp_117;
    if (!(((!temp_135 || !(sysRandomAttr.w > 0.5) ? -1 : 0)) != 0))
    {
        temp_168 = (0.0 - temp_117) + 1.0;
    }
    if (!(((!((32 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 32) || !(temp_126 > 0.5) ? -1 : 0)) != 0))
    {
        temp_169 = (0.0 - temp_117) + 1.0;
    }
    temp_170 = fma(fma(temp_54 + temp_114, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].x, 2.0, sysEmitterStaticUniformBlock.data[162].x);
    temp_171 = floatBitsToInt(1.0 / float(uint(temp_154))) + -2;
    temp_172 = sysInitRotateAttr.y;
    temp_173 = floatBitsToInt(1.0 / float(uint(temp_156))) + -2;
    temp_174 = 0;
    if (temp_129)
    {
        temp_174 = 1;
    }
    temp_175 = temp_174;
    temp_176 = ((0.0 - temp_138 < 0.0 ? 1.0 : 0.0) + (temp_138 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_130 > 0 ? -1 : 0)) + (0 - temp_130 >= 0 ? 0 : 1)));
    temp_177 = ((0.0 - temp_134 < 0.0 ? 1.0 : 0.0) + (temp_134 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_132 > 0 ? -1 : 0)) + (0 - temp_132 >= 0 ? 0 : 1)));
    temp_178 = uint(max(trunc(float(0u) * intBitsToFloat(temp_171)), 0.0));
    temp_179 = temp_136 >= sysEmitterStaticUniformBlock.data[151].w ? 1.0 : 0.0;
    temp_180 = uint(max(trunc(float(0u) * intBitsToFloat(temp_173)), 0.0));
    temp_181 = temp_175 == 1;
    temp_182 = ((0.0 - temp_146 < 0.0 ? 1.0 : 0.0) + (temp_146 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_133 > 0 ? -1 : 0)) + (0 - temp_133 >= 0 ? 0 : 1)));
    temp_183 = floatBitsToInt(1.0 / float(uint(abs(temp_154)))) + -2;
    temp_184 = temp_54;
    temp_185 = temp_114;
    temp_186 = temp_54;
    temp_187 = temp_114;
    if (temp_152)
    {
        temp_167 = temp_1;
    }
    temp_188 = temp_167;
    temp_189 = temp_136 >= sysEmitterStaticUniformBlock.data[152].w ? 1.0 : 0.0;
    if (temp_181)
    {
        temp_184 = temp_114;
    }
    temp_190 = temp_184;
    temp_191 = temp_190;
    temp_192 = temp_190;
    if (temp_181)
    {
        temp_185 = temp_126;
    }
    temp_193 = temp_185;
    temp_194 = temp_193;
    temp_195 = temp_193;
    if (temp_181)
    {
        temp_186 = temp_114;
    }
    temp_196 = temp_186;
    temp_197 = temp_196;
    temp_198 = temp_196;
    if (temp_181)
    {
        temp_187 = temp_126;
    }
    temp_199 = temp_187;
    if (!temp_181)
    {
        temp_200 = temp_175 == 2;
        if (temp_200)
        {
            temp_191 = temp_126;
        }
        temp_192 = temp_191;
        if (temp_200)
        {
            temp_194 = temp_54;
        }
        temp_195 = temp_194;
        if (temp_200)
        {
            temp_197 = temp_54;
        }
        temp_198 = temp_197;
        if (temp_200)
        {
            temp_199 = temp_114;
        }
    }
    temp_201 = floatBitsToInt(1.0 / float(uint(abs(temp_156)))) + -2;
    temp_202 = uint(max(trunc(float(0u) * intBitsToFloat(temp_183)), 0.0));
    temp_203 = uint(max(trunc(float(0u) * intBitsToFloat(temp_201)), 0.0));
    temp_204 = temp_136 >= sysEmitterStaticUniformBlock.data[153].w ? 1.0 : 0.0;
    temp_205 = 0;
    if (temp_129)
    {
        temp_205 = 2;
    }
    temp_206 = temp_205;
    temp_207 = temp_206 == 1;
    temp_208 = temp_54;
    temp_209 = temp_114;
    temp_210 = temp_54;
    temp_211 = temp_114;
    if (temp_207)
    {
        temp_208 = temp_114;
    }
    temp_212 = temp_208;
    temp_213 = temp_212;
    temp_214 = temp_212;
    if (temp_207)
    {
        temp_209 = temp_126;
    }
    temp_215 = temp_209;
    temp_216 = temp_215;
    temp_217 = temp_215;
    if (temp_207)
    {
        temp_210 = temp_114;
    }
    temp_218 = temp_210;
    temp_219 = temp_218;
    temp_220 = temp_218;
    if (temp_207)
    {
        temp_211 = temp_126;
    }
    temp_221 = temp_211;
    if (!temp_207)
    {
        temp_222 = temp_206 == 2;
        if (temp_222)
        {
            temp_213 = temp_126;
        }
        temp_214 = temp_213;
        if (temp_222)
        {
            temp_216 = temp_54;
        }
        temp_217 = temp_216;
        if (temp_222)
        {
            temp_219 = temp_54;
        }
        temp_220 = temp_219;
        if (temp_222)
        {
            temp_221 = temp_114;
        }
    }
    out_attr11.x = temp_139;
    out_attr11.y = temp_148;
    temp_223 = temp_136 >= sysEmitterStaticUniformBlock.data[154].w ? 1.0 : 0.0;
    out_attr11.z = temp_147;
    temp_224 = fma(fma(temp_170 * temp_176, -2.0, temp_170), temp_188, fma(temp_54 + -0.5, sysEmitterStaticUniformBlock.data[161].x, fma(temp_176 * temp_127, -2.0, temp_127)));
    temp_225 = int(temp_178) + int(uint(max(trunc(intBitsToFloat(temp_171) * float(uint((0 - temp_154 * int(temp_178))))), 0.0)));
    temp_226 = int(temp_202) + int(uint(max(trunc(intBitsToFloat(temp_183) * float(uint((0 - abs(temp_154) * int(temp_202))))), 0.0)));
    temp_227 = int(temp_203) + int(uint(max(trunc(intBitsToFloat(temp_201) * float(uint((0 - abs(temp_156) * int(temp_203))))), 0.0)));
    temp_228 = fma(fma(temp_165 * temp_177, -2.0, temp_165), temp_188, fma(temp_114 + -0.5, sysEmitterStaticUniformBlock.data[161].y, fma(temp_177 * temp_172, -2.0, temp_172)));
    temp_229 = fma(fma(temp_166 * temp_182, -2.0, temp_166), temp_188, fma(temp_126 + -0.5, sysEmitterStaticUniformBlock.data[161].z, fma(temp_182 * temp_128, -2.0, temp_128)));
    temp_230 = int(temp_180) + int(uint(max(trunc(intBitsToFloat(temp_173) * float(uint((0 - temp_156 * int(temp_180))))), 0.0)));
    temp_231 = fma(temp_147, NnVfx2ViewParam.data[10].z, fma(temp_148, NnVfx2ViewParam.data[10].y, temp_139 * NnVfx2ViewParam.data[10].x)) + NnVfx2ViewParam.data[10].w;
    temp_232 = fma(temp_147, NnVfx2ViewParam.data[11].z, fma(temp_148, NnVfx2ViewParam.data[11].y, temp_139 * NnVfx2ViewParam.data[11].x)) + NnVfx2ViewParam.data[11].w;
    temp_233 = (0 - int(uint(temp_154) >> 31));
    temp_234 = temp_136 >= sysEmitterStaticUniformBlock.data[155].w ? 1.0 : 0.0;
    temp_235 = (0 - int(uint(temp_156) >> 31));
    temp_236 = 1.0 / sysEmitterStaticUniformBlock.data[82].w * sysEmitterStaticUniformBlock.data[82].y;
    temp_237 = sysPosAttr.x;
    temp_238 = 1.0 / sysEmitterStaticUniformBlock.data[82].z * sysEmitterStaticUniformBlock.data[82].x;
    temp_239 = sysPosAttr.y;
    temp_240 = sysPosAttr.z;
    out_attr0.x = fma(temp_104, sysEmitterStaticUniformBlock.data[105].x, fma(fma(temp_103, (sysEmitterStaticUniformBlock.data[105].x + (0.0 - sysEmitterStaticUniformBlock.data[104].x)) * temp_102, sysEmitterStaticUniformBlock.data[104].x), temp_105, fma(temp_101, (0.0 - sysEmitterStaticUniformBlock.data[104].x), sysEmitterStaticUniformBlock.data[104].x))) * NnVfx2EmitterDynamicParam.data[0].x * sysEmitterStaticUniformBlock.data[103].x;
    temp_241 = cos(temp_228) * cos(temp_224);
    out_attr0.w = fma(temp_155, sysEmitterStaticUniformBlock.data[113].x, fma(fma((sysEmitterStaticUniformBlock.data[113].x + (0.0 - sysEmitterStaticUniformBlock.data[112].x)) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[112].w) + sysEmitterStaticUniformBlock.data[113].w)), temp_108 + (0.0 - sysEmitterStaticUniformBlock.data[112].w), sysEmitterStaticUniformBlock.data[112].x), fma(temp_153, (0.0 - temp_155), temp_153), fma(temp_153, (0.0 - sysEmitterStaticUniformBlock.data[112].x), sysEmitterStaticUniformBlock.data[112].x))) * NnVfx2EmitterDynamicParam.data[0].w;
    temp_242 = cos(temp_228) * cos(temp_229);
    temp_243 = sin(temp_224) * cos(temp_228);
    temp_244 = 1.0 / sysEmitterStaticUniformBlock.data[87].z * sysEmitterStaticUniformBlock.data[87].x;
    temp_245 = fma(temp_234, sysEmitterStaticUniformBlock.data[155].x, fma(fma(temp_223, (0.0 - temp_234), temp_223), sysEmitterStaticUniformBlock.data[154].x, fma(fma(temp_204, (0.0 - temp_223), temp_204), sysEmitterStaticUniformBlock.data[153].x, fma(fma(temp_189, (0.0 - temp_204), temp_189), sysEmitterStaticUniformBlock.data[152].x, fma(fma(temp_179, (0.0 - temp_189), temp_179), sysEmitterStaticUniformBlock.data[151].x, fma(fma(temp_164, (0.0 - temp_179), temp_164), sysEmitterStaticUniformBlock.data[150].x, fma(fma(temp_145, (0.0 - temp_164), temp_145), sysEmitterStaticUniformBlock.data[149].x, fma(fma(temp_145, (0.0 - temp_144), temp_144), sysEmitterStaticUniformBlock.data[148].x, fma(temp_144, (0.0 - sysEmitterStaticUniformBlock.data[148].x), sysEmitterStaticUniformBlock.data[148].x)))))))));
    temp_246 = sysNormalAttr.z;
    temp_247 = inversesqrt(fma(temp_240, temp_240, fma(temp_239, temp_239, temp_237 * temp_237)));
    temp_248 = 1.0 / sysEmitterStaticUniformBlock.data[87].w * sysEmitterStaticUniformBlock.data[87].y;
    temp_249 = sin(temp_224) * sin(temp_228);
    temp_250 = sin(temp_228) * cos(temp_224);
    temp_251 = sin(temp_228) * cos(temp_229);
    temp_252 = sin(temp_224) * cos(temp_229);
    temp_253 = cos(temp_224) * cos(temp_229);
    temp_254 = temp_247 * temp_239;
    temp_255 = fma(sin(temp_229), temp_241, temp_249);
    out_attr0.y = fma(temp_104, sysEmitterStaticUniformBlock.data[105].y, fma(fma(temp_103, (sysEmitterStaticUniformBlock.data[105].y + (0.0 - sysEmitterStaticUniformBlock.data[104].y)) * temp_102, sysEmitterStaticUniformBlock.data[104].y), temp_105, fma(temp_101, (0.0 - sysEmitterStaticUniformBlock.data[104].y), sysEmitterStaticUniformBlock.data[104].y))) * NnVfx2EmitterDynamicParam.data[0].y * sysEmitterStaticUniformBlock.data[103].x;
    out_attr2.x = fma(fma(temp_244, temp_150, -0.5), fma(temp_1, sysEmitterStaticUniformBlock.data[84].z, fma(temp_220, sysEmitterStaticUniformBlock.data[85].z, sysEmitterStaticUniformBlock.data[85].x + sysEmitterStaticUniformBlock.data[85].z)), fma(temp_244, float(temp_156 < 0 || !(temp_156 == 0) ? (0 - temp_156 * (temp_230 + (0 - (uint((0 - temp_156 * temp_230)) >= uint(temp_156) ? -1 : 0)))) : -1), fma(temp_1, (0.0 - sysEmitterStaticUniformBlock.data[83].x), (0.0 - fma(temp_214 * sysEmitterStaticUniformBlock.data[84].x, -2.0, sysEmitterStaticUniformBlock.data[84].x + sysEmitterStaticUniformBlock.data[83].z))))) + 0.5;
    out_attr2.y = fma(fma(temp_1, sysEmitterStaticUniformBlock.data[84].w, fma(temp_221, sysEmitterStaticUniformBlock.data[85].w, sysEmitterStaticUniformBlock.data[85].w + sysEmitterStaticUniformBlock.data[85].y)), fma(temp_248, temp_169, -0.5), (0.0 - fma(temp_248, (0.0 - float(temp_156 < 0 || !(temp_156 == 0) ? (0 - temp_235) + (temp_227 + (0 - (uint((0 - abs(temp_156) * temp_227)) >= uint(abs(temp_156)) ? -1 : 0)) ^ temp_235) : -1)), fma(temp_1, sysEmitterStaticUniformBlock.data[83].y, fma(temp_217 * sysEmitterStaticUniformBlock.data[84].y, -2.0, sysEmitterStaticUniformBlock.data[84].y + sysEmitterStaticUniformBlock.data[83].w))))) + 0.5;
    temp_256 = temp_247 * temp_237;
    temp_257 = temp_247 * temp_240;
    out_attr0.z = fma(temp_104, sysEmitterStaticUniformBlock.data[105].z, fma(fma(temp_103, (sysEmitterStaticUniformBlock.data[105].z + (0.0 - sysEmitterStaticUniformBlock.data[104].z)) * temp_102, sysEmitterStaticUniformBlock.data[104].z), temp_105, fma(temp_101, (0.0 - sysEmitterStaticUniformBlock.data[104].z), sysEmitterStaticUniformBlock.data[104].z))) * NnVfx2EmitterDynamicParam.data[0].z * sysEmitterStaticUniformBlock.data[103].x;
    temp_258 = fma(temp_245, fma(temp_254 * temp_125, 2.0, (0.0 - temp_254)), temp_239);
    temp_259 = fma(sin(temp_229), temp_243, (0.0 - temp_250));
    temp_260 = fma(sin(temp_229), temp_250, (0.0 - temp_243));
    temp_261 = sysNormalAttr.y;
    temp_262 = fma(sin(temp_229), temp_249, temp_241);
    temp_263 = sysNormalAttr.x;
    temp_264 = fma(temp_245, fma(temp_256 * temp_125, 2.0, (0.0 - temp_256)), temp_237);
    temp_265 = fma(temp_245, fma(temp_257 * temp_125, 2.0, (0.0 - temp_257)), temp_240);
    out_attr4.x = 1.0;
    out_attr4.y = 1.0;
    temp_266 = clamp(fma(1.0 / fma(fma(temp_231, 0.5, temp_232 * 0.5) * (1.0 / fma(0.0, temp_231, temp_232)), NnVfx2ViewParam.data[30].w, (0.0 - NnVfx2ViewParam.data[30].y)), (0.0 - NnVfx2ViewParam.data[30].z), (0.0 - sysEmitterStaticUniformBlock.data[137].x)) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[137].x) + sysEmitterStaticUniformBlock.data[137].y)), 0.0, 1.0);
    out_attr4.z = 1.0;
    temp_267 = fma(0.5, sysEmitterStaticUniformBlock.data[15].x, temp_264);
    temp_268 = fma(temp_95, sysEmitterStaticUniformBlock.data[142].y, fma(fma((sysEmitterStaticUniformBlock.data[142].y + (0.0 - sysEmitterStaticUniformBlock.data[141].y)) * temp_90, temp_91, sysEmitterStaticUniformBlock.data[141].y), temp_97, fma(fma(temp_93, (sysEmitterStaticUniformBlock.data[141].y + (0.0 - sysEmitterStaticUniformBlock.data[140].y)) * temp_89, sysEmitterStaticUniformBlock.data[140].y), temp_96, fma(temp_92, (0.0 - sysEmitterStaticUniformBlock.data[140].y), sysEmitterStaticUniformBlock.data[140].y)))) * sysScaleAttr.y * NnVfx2EmitterDynamicParam.data[3].z * fma(0.5, sysEmitterStaticUniformBlock.data[15].y, temp_258);
    out_attr3.x = temp_266 * NnVfx2EmitterDynamicParam.data[3].x;
    temp_269 = temp_265 == 0.0 && temp_264 == 0.0 && temp_258 == 0.0;
    temp_270 = fma(temp_95, sysEmitterStaticUniformBlock.data[142].z, fma(fma((sysEmitterStaticUniformBlock.data[142].z + (0.0 - sysEmitterStaticUniformBlock.data[141].z)) * temp_90, temp_91, sysEmitterStaticUniformBlock.data[141].z), temp_97, fma(fma(temp_93, (sysEmitterStaticUniformBlock.data[141].z + (0.0 - sysEmitterStaticUniformBlock.data[140].z)) * temp_89, sysEmitterStaticUniformBlock.data[140].z), temp_96, fma(temp_92, (0.0 - sysEmitterStaticUniformBlock.data[140].z), sysEmitterStaticUniformBlock.data[140].z)))) * sysScaleAttr.z * NnVfx2EmitterDynamicParam.data[3].w * fma(0.5, sysEmitterStaticUniformBlock.data[15].z, temp_265);
    temp_271 = (clamp(min(0.0, temp_54) + -0.0, 0.0, 1.0) + sysScaleAttr.x) * fma(temp_95, sysEmitterStaticUniformBlock.data[142].x, fma(fma((sysEmitterStaticUniformBlock.data[142].x + (0.0 - sysEmitterStaticUniformBlock.data[141].x)) * temp_90, temp_91, sysEmitterStaticUniformBlock.data[141].x), temp_97, fma(fma(temp_93, (sysEmitterStaticUniformBlock.data[141].x + (0.0 - sysEmitterStaticUniformBlock.data[140].x)) * temp_89, sysEmitterStaticUniformBlock.data[140].x), temp_96, fma(temp_92, (0.0 - sysEmitterStaticUniformBlock.data[140].x), sysEmitterStaticUniformBlock.data[140].x)))) * NnVfx2EmitterDynamicParam.data[3].y * temp_267;
    temp_272 = sin(temp_229) * (0.0 - temp_268);
    temp_273 = temp_268 * temp_253;
    temp_274 = temp_268 * temp_252;
    temp_275 = 0.0 * temp_268;
    temp_276 = temp_273;
    temp_277 = temp_274;
    temp_278 = temp_275;
    temp_279 = temp_267;
    temp_280 = temp_257;
    temp_281 = temp_272;
    if (temp_269)
    {
        temp_276 = temp_246;
    }
    temp_282 = temp_276;
    if (!temp_269)
    {
        temp_282 = fma(temp_265, sysEmitterStaticUniformBlock.data[14].y, temp_246);
    }
    temp_283 = temp_282;
    if (temp_269)
    {
        temp_277 = temp_263;
    }
    temp_284 = temp_277;
    if (!temp_269)
    {
        temp_284 = fma(temp_264, sysEmitterStaticUniformBlock.data[14].y, temp_263);
    }
    temp_285 = temp_284;
    if (temp_269)
    {
        temp_278 = temp_261;
    }
    temp_286 = temp_278;
    if (!temp_269)
    {
        temp_279 = fma(temp_264, sysEmitterStaticUniformBlock.data[14].y, temp_263);
    }
    temp_287 = temp_279;
    if (!temp_269)
    {
        temp_286 = fma(temp_258, sysEmitterStaticUniformBlock.data[14].y, temp_261);
    }
    temp_288 = temp_286;
    if (!temp_269)
    {
        temp_280 = fma(temp_265, sysEmitterStaticUniformBlock.data[14].y, temp_246);
    }
    temp_289 = temp_280;
    if (temp_269)
    {
        temp_281 = temp_261;
    }
    temp_290 = temp_281;
    if (!temp_269)
    {
        temp_290 = fma(temp_258, sysEmitterStaticUniformBlock.data[14].y, temp_261);
    }
    temp_291 = temp_290;
    temp_292 = fma(0.0, (0.0 - temp_285), temp_283);
    temp_293 = 0.0 + fma(temp_251, temp_270, fma(temp_271, temp_242, temp_272));
    temp_294 = fma(0.0, temp_285, (0.0 - temp_288));
    temp_295 = fma(0.0, temp_288, 0.0 * (0.0 - temp_283));
    temp_296 = 0.0 + fma(temp_260, temp_270, fma(temp_255, temp_271, temp_273));
    if (temp_269)
    {
        temp_287 = temp_263;
    }
    temp_297 = temp_287;
    if (temp_269)
    {
        temp_289 = temp_246;
    }
    temp_298 = temp_289;
    temp_299 = 0.0 + fma(temp_262, temp_270, fma(temp_259, temp_271, temp_274));
    temp_300 = inversesqrt(fma(temp_294, temp_294, fma(temp_292, temp_292, temp_295 * temp_295)));
    temp_301 = fma(0.0, temp_270, fma(0.0, temp_271, temp_275)) + 1.0;
    temp_302 = 0.0 + fma(temp_251, temp_298, fma(temp_242, temp_297, sin(temp_229) * (0.0 - temp_291)));
    temp_303 = 0.0 + fma(temp_260, temp_298, fma(temp_255, temp_297, temp_253 * temp_291));
    temp_304 = temp_292 * temp_300;
    temp_305 = fma(temp_139, temp_301, fma(temp_299, temp_71, fma(temp_296, temp_68, temp_293 * temp_67)));
    temp_306 = fma(temp_147, temp_301, fma(temp_299, temp_79, fma(temp_296, temp_76, temp_293 * temp_77)));
    out_attr5.x = temp_305;
    temp_307 = fma(temp_148, temp_301, fma(temp_299, temp_62, fma(temp_296, temp_58, temp_293 * temp_59)));
    out_attr5.z = temp_306;
    out_attr5.y = temp_307;
    temp_308 = 0.0 + fma(temp_262, temp_298, fma(temp_259, temp_297, temp_252 * temp_291));
    temp_309 = temp_295 * temp_300;
    temp_310 = temp_294 * temp_300;
    out_attr10.x = sysCustomShaderUniformBlock0.data[36].w;
    temp_311 = fma(temp_306, NnVfx2ViewParam.data[0].z, fma(temp_307, NnVfx2ViewParam.data[0].y, temp_305 * NnVfx2ViewParam.data[0].x)) + NnVfx2ViewParam.data[0].w;
    out_attr6.z = fma(0.0, temp_147, fma(temp_308, temp_79, fma(temp_303, temp_76, temp_302 * temp_77)));
    temp_312 = fma(temp_306, NnVfx2ViewParam.data[1].z, fma(temp_307, NnVfx2ViewParam.data[1].y, temp_305 * NnVfx2ViewParam.data[1].x)) + NnVfx2ViewParam.data[1].w;
    out_attr9.x = (0.0 - fma(temp_306, sysCustomShaderUniformBlock0.data[38].z, fma(temp_307, sysCustomShaderUniformBlock0.data[38].y, temp_305 * sysCustomShaderUniformBlock0.data[38].x))) + -0.0;
    temp_313 = fma(temp_306, NnVfx2ViewParam.data[2].z, fma(temp_307, NnVfx2ViewParam.data[2].y, temp_305 * NnVfx2ViewParam.data[2].x)) + NnVfx2ViewParam.data[2].w;
    temp_314 = 0.0 + fma(temp_260, temp_310, fma(temp_255, temp_309, temp_253 * temp_304));
    temp_315 = 0.0 + fma(temp_251, temp_310, fma(temp_242, temp_309, sin(temp_229) * (0.0 - temp_304)));
    temp_316 = inversesqrt(fma(temp_313, temp_313, fma(temp_312, temp_312, temp_311 * temp_311)));
    temp_317 = 0.0 + fma(temp_262, temp_310, fma(temp_259, temp_309, temp_252 * temp_304));
    temp_318 = fma(temp_306, NnVfx2ViewParam.data[3].z, fma(temp_307, NnVfx2ViewParam.data[3].y, temp_305 * NnVfx2ViewParam.data[3].x)) + NnVfx2ViewParam.data[3].w;
    out_attr7.z = fma(0.0, temp_147, fma(temp_259, temp_79, fma(temp_255, temp_76, temp_242 * temp_77)));
    out_attr7.y = fma(0.0, temp_148, fma(temp_259, temp_62, fma(temp_255, temp_58, temp_242 * temp_59)));
    out_attr7.x = fma(0.0, temp_139, fma(temp_259, temp_71, fma(temp_255, temp_68, temp_242 * temp_67)));
    out_attr1.z = fma(fma(temp_238, temp_149, -0.5), fma(temp_1, sysEmitterStaticUniformBlock.data[79].z, fma(temp_198, sysEmitterStaticUniformBlock.data[80].z, sysEmitterStaticUniformBlock.data[80].z + sysEmitterStaticUniformBlock.data[80].x)), fma(temp_238, float(temp_154 < 0 || !(temp_154 == 0) ? (0 - temp_154 * (temp_225 + (0 - (uint((0 - temp_154 * temp_225)) >= uint(temp_154) ? -1 : 0)))) : -1), fma(temp_1, (0.0 - sysEmitterStaticUniformBlock.data[78].x), (0.0 - fma(temp_192 * sysEmitterStaticUniformBlock.data[79].x, -2.0, sysEmitterStaticUniformBlock.data[79].x + sysEmitterStaticUniformBlock.data[78].z))))) + 0.5;
    out_attr1.w = fma(fma(temp_1, sysEmitterStaticUniformBlock.data[79].w, fma(temp_199, sysEmitterStaticUniformBlock.data[80].w, sysEmitterStaticUniformBlock.data[80].w + sysEmitterStaticUniformBlock.data[80].y)), fma(temp_236, temp_168, -0.5), (0.0 - fma(temp_236, (0.0 - float(temp_154 < 0 || !(temp_154 == 0) ? (0 - temp_233) + (temp_226 + (0 - (uint((0 - abs(temp_154) * temp_226)) >= uint(abs(temp_154)) ? -1 : 0)) ^ temp_233) : -1)), fma(temp_1, sysEmitterStaticUniformBlock.data[78].y, fma(temp_195 * sysEmitterStaticUniformBlock.data[79].y, -2.0, sysEmitterStaticUniformBlock.data[79].y + sysEmitterStaticUniformBlock.data[78].w))))) + 0.5;
    out_attr6.y = fma(0.0, temp_148, fma(temp_308, temp_62, fma(temp_303, temp_58, temp_302 * temp_59)));
    out_attr6.x = fma(0.0, temp_139, fma(temp_308, temp_71, fma(temp_303, temp_68, temp_302 * temp_67)));
    gl_Position.w = fma(temp_318, NnVfx2ViewParam.data[7].w, fma(temp_313, NnVfx2ViewParam.data[7].z, fma(temp_312, NnVfx2ViewParam.data[7].y, temp_311 * NnVfx2ViewParam.data[7].x)));
    gl_Position.z = fma(temp_318, NnVfx2ViewParam.data[6].w, fma(temp_313, NnVfx2ViewParam.data[6].z, fma(temp_312, NnVfx2ViewParam.data[6].y, temp_311 * NnVfx2ViewParam.data[6].x)));
    gl_Position.y = fma(temp_318, NnVfx2ViewParam.data[5].w, fma(temp_313, NnVfx2ViewParam.data[5].z, fma(temp_312, NnVfx2ViewParam.data[5].y, temp_311 * NnVfx2ViewParam.data[5].x)));
    gl_Position.x = fma(temp_318, NnVfx2ViewParam.data[4].w, fma(temp_313, NnVfx2ViewParam.data[4].z, fma(temp_312, NnVfx2ViewParam.data[4].y, temp_311 * NnVfx2ViewParam.data[4].x)));
    out_attr13.x = temp_311 * temp_316;
    out_attr13.y = temp_312 * temp_316;
    out_attr13.z = temp_313 * temp_316;
    out_attr8.z = fma(0.0, temp_147, fma(temp_317, temp_79, fma(temp_314, temp_76, temp_315 * temp_77)));
    out_attr8.y = fma(0.0, temp_148, fma(temp_317, temp_62, fma(temp_314, temp_58, temp_315 * temp_59)));
    if (0.0 < sysCustomShaderUniformBlock1.data[4].w)
    {
        temp_319 = (0.0 - temp_139) + temp_305;
        temp_320 = (0.0 - temp_148) + temp_307;
        temp_321 = (0.0 - temp_147) + temp_306;
        out_attr12.x = fma(fma(temp_321, NnVfx2ViewParam.data[0].z, fma(temp_320, NnVfx2ViewParam.data[0].y, temp_319 * NnVfx2ViewParam.data[0].x)), sysCustomShaderUniformBlock0.data[31].x, 0.5) * sysCustomShaderUniformBlock0.data[41].x;
        out_attr12.y = fma(fma(temp_321, NnVfx2ViewParam.data[1].z, fma(temp_320, NnVfx2ViewParam.data[1].y, temp_319 * NnVfx2ViewParam.data[1].x)), (0.0 - sysCustomShaderUniformBlock0.data[31].y), 0.5) * sysCustomShaderUniformBlock0.data[41].x;
    }
    out_attr8.x = fma(0.0, temp_139, fma(temp_317, temp_71, fma(temp_314, temp_68, temp_315 * temp_67)));
    if (!(temp_266 <= 0.0))
    {
        return;
    }
    gl_Position.x = 0.0;
    gl_Position.y = 0.0;
    gl_Position.z = NnVfx2ViewParam.data[30].y * 5.0;
    out_attr3.x = 0.0;
    return;
}
