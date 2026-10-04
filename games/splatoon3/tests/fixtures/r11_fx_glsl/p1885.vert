// static_grsn.bfsha model VfxGeneralShader program 1885 (vert)
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
    bool temp_21;
    precise float temp_22;
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
    precise float temp_109;
    precise float temp_110;
    precise float temp_111;
    precise float temp_112;
    precise float temp_113;
    precise float temp_114;
    bool temp_115;
    precise float temp_116;
    int temp_117;
    precise float temp_118;
    precise float temp_119;
    precise float temp_120;
    precise float temp_121;
    precise float temp_122;
    precise float temp_123;
    bool temp_124;
    precise float temp_125;
    int temp_126;
    int temp_127;
    precise float temp_128;
    precise float temp_129;
    precise float temp_130;
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
    precise vec2 temp_174;
    precise float temp_175;
    precise float temp_176;
    precise float temp_177;
    precise float temp_178;
    precise float temp_179;
    int temp_180;
    precise float temp_181;
    int temp_182;
    precise float temp_183;
    precise float temp_184;
    bool temp_185;
    precise float temp_186;
    bool temp_187;
    precise float temp_188;
    int temp_189;
    precise float temp_190;
    precise float temp_191;
    precise float temp_192;
    precise float temp_193;
    precise float temp_194;
    int temp_195;
    precise float temp_196;
    int temp_197;
    precise float temp_198;
    int temp_199;
    precise float temp_200;
    precise float temp_201;
    int temp_202;
    int temp_203;
    uint temp_204;
    bool temp_205;
    bool temp_206;
    uint temp_207;
    uint temp_208;
    uint temp_209;
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
    precise float temp_222;
    precise float temp_223;
    precise float temp_224;
    precise float temp_225;
    precise float temp_226;
    precise float temp_227;
    bool temp_228;
    precise float temp_229;
    precise float temp_230;
    precise float temp_231;
    precise float temp_232;
    precise float temp_233;
    int temp_234;
    precise float temp_235;
    int temp_236;
    int temp_237;
    precise float temp_238;
    precise float temp_239;
    precise float temp_240;
    precise float temp_241;
    precise float temp_242;
    int temp_243;
    precise float temp_244;
    precise float temp_245;
    precise float temp_246;
    precise float temp_247;
    precise float temp_248;
    int temp_249;
    precise float temp_250;
    precise float temp_251;
    precise float temp_252;
    precise float temp_253;
    precise float temp_254;
    precise float temp_255;
    int temp_256;
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
    bool temp_271;
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
    bool temp_290;
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
    temp_9 = sysEmtMat1Attr.x;
    temp_10 = sysEmtMat2Attr.x;
    temp_11 = sysEmtMat0Attr.y;
    temp_12 = sysEmtMat1Attr.y;
    temp_13 = sysEmtMat2Attr.y;
    temp_14 = sysEmtMat0Attr.z;
    temp_15 = sysEmtMat1Attr.z;
    temp_16 = sysEmtMat2Attr.z;
    temp_17 = fma(temp_14, temp_14, fma(temp_11, temp_11, temp_7 * temp_7));
    temp_18 = fma(temp_15, temp_15, fma(temp_12, temp_12, temp_9 * temp_9));
    temp_19 = fma(temp_16, temp_16, fma(temp_13, temp_13, temp_10 * temp_10));
    temp_20 = sqrt(temp_17) > 0.0;
    temp_21 = sqrt(temp_18) > 0.0;
    temp_22 = sysScaleAttr.w;
    temp_23 = temp_1 + NnVfx2EmitterDynamicParam.data[2].w;
    temp_24 = intBitsToFloat(undef);
    temp_25 = sqrt(temp_19);
    temp_26 = sqrt(temp_17);
    if (temp_20)
    {
        temp_24 = inversesqrt(temp_17);
    }
    temp_27 = temp_24;
    temp_28 = sqrt(temp_19) > 0.0;
    temp_29 = intBitsToFloat(undef);
    temp_30 = temp_27;
    if (temp_21)
    {
        temp_29 = inversesqrt(temp_18);
    }
    temp_31 = temp_29;
    temp_32 = temp_31;
    if (temp_8)
    {
        temp_25 = temp_23 * temp_23;
    }
    temp_33 = temp_25;
    temp_34 = temp_33;
    if (temp_8)
    {
        temp_34 = temp_33 * sysEmitterStaticUniformBlock.data[13].w;
    }
    temp_35 = temp_34;
    temp_36 = intBitsToFloat(undef);
    if (temp_28)
    {
        temp_36 = inversesqrt(temp_19);
    }
    temp_37 = temp_36;
    temp_38 = intBitsToFloat(undef);
    temp_39 = temp_37;
    if (temp_8)
    {
        temp_38 = temp_35 * 0.5 * sysEmitterStaticUniformBlock.data[13].y;
    }
    temp_40 = intBitsToFloat(undef);
    temp_41 = temp_38;
    if (temp_8)
    {
        temp_40 = temp_35 * 0.5 * sysEmitterStaticUniformBlock.data[13].z;
    }
    temp_42 = temp_40;
    if (temp_8)
    {
        temp_26 = temp_35 * 0.5 * sysEmitterStaticUniformBlock.data[13].x;
    }
    temp_43 = temp_26;
    if (!temp_8)
    {
        temp_44 = 1.0 / log2(sysEmitterStaticUniformBlock.data[14].x) * 1.44269502;
        temp_45 = (temp_23 + (0.0 - fma(temp_44, exp2(temp_23 * log2(abs(sysEmitterStaticUniformBlock.data[14].x))), (0.0 - temp_44)))) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[14].x) + 1.0)) * sysEmitterStaticUniformBlock.data[13].w;
        temp_41 = temp_45 * sysEmitterStaticUniformBlock.data[13].y;
        temp_43 = temp_45 * sysEmitterStaticUniformBlock.data[13].x;
        temp_42 = temp_45 * sysEmitterStaticUniformBlock.data[13].z;
    }
    temp_46 = temp_41;
    temp_47 = temp_43;
    temp_48 = temp_42;
    temp_49 = intBitsToFloat(undef);
    if (temp_21)
    {
        temp_49 = temp_31 * temp_12;
    }
    temp_50 = sysRandomAttr.x;
    temp_51 = intBitsToFloat(undef);
    temp_52 = temp_49;
    if (temp_20)
    {
        temp_51 = temp_27 * temp_9;
    }
    temp_53 = temp_51;
    if (!temp_21)
    {
        temp_52 = 0.0;
    }
    temp_54 = temp_52;
    if (!temp_20)
    {
        temp_53 = 0.0;
    }
    temp_55 = temp_53;
    temp_56 = intBitsToFloat(undef);
    if (temp_28)
    {
        temp_56 = temp_37 * temp_15;
    }
    temp_57 = temp_56;
    if (!temp_28)
    {
        temp_57 = 0.0;
    }
    temp_58 = temp_57;
    temp_59 = intBitsToFloat(undef);
    if (temp_20)
    {
        temp_59 = temp_27 * temp_7;
    }
    temp_60 = intBitsToFloat(undef);
    temp_61 = temp_59;
    if (temp_21)
    {
        temp_60 = temp_31 * temp_11;
    }
    temp_62 = temp_60;
    if (!temp_20)
    {
        temp_61 = 0.0;
    }
    temp_63 = temp_61;
    if (!temp_21)
    {
        temp_62 = 0.0;
    }
    temp_64 = temp_62;
    temp_65 = intBitsToFloat(undef);
    if (temp_28)
    {
        temp_65 = temp_37 * temp_14;
    }
    temp_66 = temp_65;
    if (!temp_28)
    {
        temp_66 = 0.0;
    }
    temp_67 = temp_66;
    if (temp_21)
    {
        temp_32 = temp_31 * temp_13;
    }
    temp_68 = temp_32;
    if (temp_20)
    {
        temp_30 = temp_27 * temp_10;
    }
    temp_69 = fma(temp_47, temp_64, temp_46 * temp_54);
    temp_70 = temp_30;
    temp_71 = temp_69;
    if (!temp_21)
    {
        temp_68 = 0.0;
    }
    temp_72 = temp_68;
    if (!temp_20)
    {
        temp_70 = 0.0;
    }
    temp_73 = temp_70;
    if (temp_28)
    {
        temp_39 = temp_37 * temp_16;
    }
    temp_74 = temp_39;
    if (!temp_28)
    {
        temp_74 = 0.0;
    }
    temp_75 = temp_74;
    if (temp_8)
    {
        temp_71 = temp_23;
    }
    temp_76 = temp_71;
    if (!temp_8)
    {
        temp_77 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[14].x) + 1.0);
        temp_76 = fma(exp2(temp_23 * log2(abs(sysEmitterStaticUniformBlock.data[14].x))), (0.0 - temp_77), temp_77);
    }
    temp_78 = temp_76;
    temp_79 = fma(fma(temp_78, sysLocalVecAttr.x, fma(temp_48, temp_73, fma(temp_47, temp_63, temp_46 * temp_55))), temp_22, sysLocalPosAttr.x);
    temp_80 = fma(fma(temp_78, sysLocalVecAttr.y, fma(temp_48, temp_72, temp_69)), temp_22, sysLocalPosAttr.y);
    temp_81 = fma(fma(temp_78, sysLocalVecAttr.z, fma(temp_48, temp_75, fma(temp_47, temp_67, temp_46 * temp_58))), temp_22, sysLocalPosAttr.z);
    if (0.0 < sysEmitterStaticUniformBlock.data[11].x)
    {
        temp_82 = fma(temp_50 * sysEmitterStaticUniformBlock.data[12].y, sysEmitterStaticUniformBlock.data[11].x, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[11].x);
        temp_83 = temp_82 + (0.0 - floor(temp_82));
    }
    else
    {
        temp_83 = temp_1 * (1.0 / temp_2);
    }
    temp_84 = temp_83;
    temp_85 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[140].w) + sysEmitterStaticUniformBlock.data[141].w);
    temp_86 = 1.0 / (sysEmitterStaticUniformBlock.data[142].w + (0.0 - sysEmitterStaticUniformBlock.data[141].w));
    temp_87 = temp_84 >= sysEmitterStaticUniformBlock.data[140].w ? 1.0 : 0.0;
    temp_88 = temp_84 >= sysEmitterStaticUniformBlock.data[141].w ? 1.0 : 0.0;
    temp_89 = temp_84 + (0.0 - sysEmitterStaticUniformBlock.data[140].w);
    temp_90 = temp_84 >= sysEmitterStaticUniformBlock.data[142].w ? 1.0 : 0.0;
    temp_91 = temp_84 + (0.0 - sysEmitterStaticUniformBlock.data[141].w);
    temp_92 = fma(temp_87, (0.0 - temp_88), temp_87);
    temp_93 = fma(temp_88, (0.0 - temp_90), temp_88);
    if (0.0 < sysEmitterStaticUniformBlock.data[10].x)
    {
        temp_94 = fma(temp_50 * sysEmitterStaticUniformBlock.data[11].y, sysEmitterStaticUniformBlock.data[10].x, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[10].x);
        temp_95 = temp_94 + (0.0 - floor(temp_94));
    }
    else
    {
        temp_95 = temp_1 * (1.0 / temp_2);
    }
    temp_96 = temp_95;
    temp_97 = temp_96 >= sysEmitterStaticUniformBlock.data[104].w ? 1.0 : 0.0;
    temp_98 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[104].w) + sysEmitterStaticUniformBlock.data[105].w);
    temp_99 = temp_96 + (0.0 - sysEmitterStaticUniformBlock.data[104].w);
    temp_100 = temp_96 >= sysEmitterStaticUniformBlock.data[105].w ? 1.0 : 0.0;
    temp_101 = fma(temp_97, (0.0 - temp_100), temp_97);
    temp_102 = fma(temp_100, sysEmitterStaticUniformBlock.data[105].z, fma(fma(temp_99, (sysEmitterStaticUniformBlock.data[105].z + (0.0 - sysEmitterStaticUniformBlock.data[104].z)) * temp_98, sysEmitterStaticUniformBlock.data[104].z), temp_101, fma(temp_97, (0.0 - sysEmitterStaticUniformBlock.data[104].z), sysEmitterStaticUniformBlock.data[104].z)));
    temp_103 = temp_102;
    if (0.0 < sysEmitterStaticUniformBlock.data[10].y)
    {
        temp_104 = fma(temp_50 * sysEmitterStaticUniformBlock.data[11].z, sysEmitterStaticUniformBlock.data[10].y, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[10].y);
        temp_105 = temp_104 + (0.0 - floor(temp_104));
    }
    else
    {
        temp_105 = temp_1 * (1.0 / temp_2);
    }
    temp_106 = temp_105;
    temp_107 = temp_106 >= sysEmitterStaticUniformBlock.data[112].w ? 1.0 : 0.0;
    temp_108 = temp_106 >= sysEmitterStaticUniformBlock.data[113].w ? 1.0 : 0.0;
    temp_109 = temp_106 >= sysEmitterStaticUniformBlock.data[114].w ? 1.0 : 0.0;
    out_attr0.x = fma(temp_100, sysEmitterStaticUniformBlock.data[105].x, fma(fma(temp_99, (sysEmitterStaticUniformBlock.data[105].x + (0.0 - sysEmitterStaticUniformBlock.data[104].x)) * temp_98, sysEmitterStaticUniformBlock.data[104].x), temp_101, fma(temp_97, (0.0 - sysEmitterStaticUniformBlock.data[104].x), sysEmitterStaticUniformBlock.data[104].x))) * NnVfx2EmitterDynamicParam.data[0].x * sysEmitterStaticUniformBlock.data[103].x;
    out_attr0.y = fma(temp_100, sysEmitterStaticUniformBlock.data[105].y, fma(fma(temp_99, (sysEmitterStaticUniformBlock.data[105].y + (0.0 - sysEmitterStaticUniformBlock.data[104].y)) * temp_98, sysEmitterStaticUniformBlock.data[104].y), temp_101, fma(temp_97, (0.0 - sysEmitterStaticUniformBlock.data[104].y), sysEmitterStaticUniformBlock.data[104].y))) * NnVfx2EmitterDynamicParam.data[0].y * sysEmitterStaticUniformBlock.data[103].x;
    out_attr0.z = temp_102 * NnVfx2EmitterDynamicParam.data[0].z * sysEmitterStaticUniformBlock.data[103].x;
    out_attr0.w = fma(temp_109, sysEmitterStaticUniformBlock.data[114].x, fma(fma(((0.0 - sysEmitterStaticUniformBlock.data[113].x) + sysEmitterStaticUniformBlock.data[114].x) * (1.0 / (sysEmitterStaticUniformBlock.data[114].w + (0.0 - sysEmitterStaticUniformBlock.data[113].w))), temp_106 + (0.0 - sysEmitterStaticUniformBlock.data[113].w), sysEmitterStaticUniformBlock.data[113].x), fma(temp_108, (0.0 - temp_109), temp_108), fma(fma((sysEmitterStaticUniformBlock.data[113].x + (0.0 - sysEmitterStaticUniformBlock.data[112].x)) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[112].w) + sysEmitterStaticUniformBlock.data[113].w)), temp_106 + (0.0 - sysEmitterStaticUniformBlock.data[112].w), sysEmitterStaticUniformBlock.data[112].x), fma(temp_108, (0.0 - temp_107), temp_107), fma(temp_107, (0.0 - sysEmitterStaticUniformBlock.data[112].x), sysEmitterStaticUniformBlock.data[112].x)))) * NnVfx2EmitterDynamicParam.data[0].w;
    if (0.0 < sysEmitterStaticUniformBlock.data[10].w)
    {
        temp_110 = fma(temp_50 * sysEmitterStaticUniformBlock.data[12].x, sysEmitterStaticUniformBlock.data[10].w, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[10].w);
        temp_111 = temp_110 + (0.0 - floor(temp_110));
    }
    else
    {
        temp_111 = temp_1 * (1.0 / temp_2);
    }
    temp_112 = temp_111;
    temp_113 = sysRandomAttr.y;
    temp_114 = sysRandomAttr.z;
    temp_115 = 0.0 == sysEmitterStaticUniformBlock.data[162].w;
    temp_116 = floor(temp_50 * 2.0);
    temp_117 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x20000000;
    temp_118 = sysInitRotateAttr.y;
    temp_119 = sysInitRotateAttr.z;
    temp_120 = sysInitRotateAttr.x;
    temp_121 = sysPosAttr.z;
    temp_122 = sysPosAttr.x;
    temp_123 = sysPosAttr.y;
    temp_124 = sysEmitterStaticUniformBlock.data[162].w == 1.0;
    temp_125 = floor(temp_113 * 2.0);
    temp_126 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x40000000;
    temp_127 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x10000000;
    temp_128 = intBitsToFloat(temp_126);
    temp_129 = sysEmitterStaticUniformBlock.data[162].w;
    if (temp_115)
    {
        temp_103 = 1.0;
    }
    temp_130 = temp_103;
    if (!temp_115)
    {
        temp_128 = log2(abs(sysEmitterStaticUniformBlock.data[162].w));
    }
    temp_131 = temp_128;
    temp_132 = temp_114 * 2.0;
    temp_133 = temp_131;
    temp_134 = temp_132;
    if (!temp_115)
    {
        temp_133 = temp_1 * temp_131;
    }
    if (!temp_124)
    {
        temp_134 = (0.0 - sysEmitterStaticUniformBlock.data[162].w) + 1.0;
    }
    temp_135 = temp_134;
    temp_136 = ((0.0 - temp_116 < 0.0 ? 1.0 : 0.0) + (temp_116 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_117 > 0 ? -1 : 0)) + (0 - temp_117 >= 0 ? 0 : 1)));
    temp_137 = temp_135;
    if (!temp_124)
    {
        temp_137 = 1.0 / temp_135;
    }
    temp_138 = float(abs((0 - (temp_126 > 0 ? -1 : 0)) + (0 - temp_126 >= 0 ? 0 : 1))) * ((0.0 - temp_125 < 0.0 ? 1.0 : 0.0) + (temp_125 > 0.0 ? 1.0 : 0.0));
    if (!temp_115)
    {
        temp_130 = exp2(temp_133);
    }
    temp_139 = fma(fma(temp_113 + temp_114, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].y, 2.0, sysEmitterStaticUniformBlock.data[162].y);
    if (temp_124)
    {
        temp_129 = temp_1;
    }
    temp_140 = fma(fma(temp_50 + temp_114, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].z, 2.0, sysEmitterStaticUniformBlock.data[162].z);
    temp_141 = ((0.0 - floor(temp_132) < 0.0 ? 1.0 : 0.0) + (floor(temp_132) > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_127 > 0 ? -1 : 0)) + (0 - temp_127 >= 0 ? 0 : 1)));
    temp_142 = fma(fma(temp_50 + temp_113, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].x, 2.0, sysEmitterStaticUniformBlock.data[162].x);
    temp_143 = temp_129;
    if (!temp_124)
    {
        temp_143 = fma(temp_137, (0.0 - temp_130), temp_137);
    }
    temp_144 = temp_143;
    temp_145 = fma(fma(temp_139 * temp_136, -2.0, temp_139), temp_144, fma(temp_113 + -0.5, sysEmitterStaticUniformBlock.data[161].y, fma(temp_136 * temp_118, -2.0, temp_118)));
    temp_146 = fma(fma(temp_140 * temp_138, -2.0, temp_140), temp_144, fma(temp_114 + -0.5, sysEmitterStaticUniformBlock.data[161].z, fma(temp_138 * temp_119, -2.0, temp_119)));
    temp_147 = fma(temp_90, sysEmitterStaticUniformBlock.data[142].y, fma(fma((sysEmitterStaticUniformBlock.data[142].y + (0.0 - sysEmitterStaticUniformBlock.data[141].y)) * temp_86, temp_91, sysEmitterStaticUniformBlock.data[141].y), temp_93, fma(fma(temp_89, (sysEmitterStaticUniformBlock.data[141].y + (0.0 - sysEmitterStaticUniformBlock.data[140].y)) * temp_85, sysEmitterStaticUniformBlock.data[140].y), temp_92, fma(temp_87, (0.0 - sysEmitterStaticUniformBlock.data[140].y), sysEmitterStaticUniformBlock.data[140].y)))) * sysScaleAttr.y * NnVfx2EmitterDynamicParam.data[3].z * fma(0.5, sysEmitterStaticUniformBlock.data[15].y, temp_123);
    temp_148 = fma(fma(temp_142 * temp_141, -2.0, temp_142), temp_144, fma(temp_50 + -0.5, sysEmitterStaticUniformBlock.data[161].x, fma(temp_141 * temp_120, -2.0, temp_120)));
    temp_149 = fma(temp_90, sysEmitterStaticUniformBlock.data[142].z, fma(fma((sysEmitterStaticUniformBlock.data[142].z + (0.0 - sysEmitterStaticUniformBlock.data[141].z)) * temp_86, temp_91, sysEmitterStaticUniformBlock.data[141].z), temp_93, fma(fma(temp_89, (sysEmitterStaticUniformBlock.data[141].z + (0.0 - sysEmitterStaticUniformBlock.data[140].z)) * temp_85, sysEmitterStaticUniformBlock.data[140].z), temp_92, fma(temp_87, (0.0 - sysEmitterStaticUniformBlock.data[140].z), sysEmitterStaticUniformBlock.data[140].z)))) * sysScaleAttr.z * NnVfx2EmitterDynamicParam.data[3].w * fma(0.5, sysEmitterStaticUniformBlock.data[15].z, temp_121);
    temp_150 = (clamp(min(0.0, temp_50) + -0.0, 0.0, 1.0) + sysScaleAttr.x) * fma(temp_90, sysEmitterStaticUniformBlock.data[142].x, fma(fma((sysEmitterStaticUniformBlock.data[142].x + (0.0 - sysEmitterStaticUniformBlock.data[141].x)) * temp_86, temp_91, sysEmitterStaticUniformBlock.data[141].x), temp_93, fma(fma(temp_89, (sysEmitterStaticUniformBlock.data[141].x + (0.0 - sysEmitterStaticUniformBlock.data[140].x)) * temp_85, sysEmitterStaticUniformBlock.data[140].x), temp_92, fma(temp_87, (0.0 - sysEmitterStaticUniformBlock.data[140].x), sysEmitterStaticUniformBlock.data[140].x)))) * NnVfx2EmitterDynamicParam.data[3].y * fma(0.5, sysEmitterStaticUniformBlock.data[15].x, temp_122);
    temp_151 = cos(temp_145) * sin(temp_146);
    temp_152 = cos(temp_146) * sin(temp_145);
    temp_153 = cos(temp_145) * cos(temp_146);
    temp_154 = sin(temp_146) * sin(temp_145);
    temp_155 = cos(temp_146) * cos(temp_148);
    temp_156 = sin(temp_146) * cos(temp_148);
    temp_157 = sin(temp_145) * cos(temp_148);
    temp_158 = fma(sin(temp_148), temp_152, (0.0 - temp_151));
    temp_159 = fma(sin(temp_148), temp_151, (0.0 - temp_152));
    temp_160 = fma(sin(temp_148), temp_154, temp_153);
    temp_161 = fma(sin(temp_148), temp_153, temp_154);
    temp_162 = cos(temp_145) * cos(temp_148);
    temp_163 = fma(temp_81, temp_14, fma(temp_80, temp_11, temp_79 * temp_7)) + sysEmtMat0Attr.w;
    temp_164 = fma(temp_81, temp_15, fma(temp_80, temp_12, temp_79 * temp_9)) + sysEmtMat1Attr.w;
    temp_165 = 0.0 + fma(sin(temp_148), temp_147, fma(temp_150, temp_156, temp_149 * temp_155));
    temp_166 = 0.0 + fma(temp_147, (0.0 - temp_157), fma(temp_160, temp_150, temp_158 * temp_149));
    temp_167 = fma(temp_81, temp_16, fma(temp_80, temp_13, temp_79 * temp_10)) + sysEmtMat2Attr.w;
    temp_168 = 0.0 + fma(temp_162, (0.0 - temp_147), fma(temp_159, temp_150, temp_161 * temp_149));
    temp_169 = fma(0.0, (0.0 - temp_147), fma(0.0, temp_150, 0.0 * temp_149)) + 1.0;
    temp_170 = fma(temp_163, temp_169, fma(temp_168, temp_67, fma(temp_165, temp_64, temp_166 * temp_63)));
    temp_171 = fma(temp_164, temp_169, fma(temp_168, temp_58, fma(temp_165, temp_54, temp_166 * temp_55)));
    temp_172 = fma(temp_167, temp_169, fma(temp_168, temp_75, fma(temp_165, temp_72, temp_166 * temp_73)));
    temp_173 = 1.0 / (fma(temp_172, sysCustomShaderUniformBlock0.data[5].z, fma(temp_171, sysCustomShaderUniformBlock0.data[5].y, temp_170 * sysCustomShaderUniformBlock0.data[5].x)) + sysCustomShaderUniformBlock0.data[5].w);
    temp_174 = texture(sysCustomShaderTextureSampler1, vec2((fma(temp_172, sysCustomShaderUniformBlock0.data[2].z, fma(temp_171, sysCustomShaderUniformBlock0.data[2].y, temp_170 * sysCustomShaderUniformBlock0.data[2].x)) + sysCustomShaderUniformBlock0.data[2].w) * temp_173, (fma(temp_172, sysCustomShaderUniformBlock0.data[3].z, fma(temp_171, sysCustomShaderUniformBlock0.data[3].y, temp_170 * sysCustomShaderUniformBlock0.data[3].x)) + sysCustomShaderUniformBlock0.data[3].w) * temp_173)).xy;
    temp_175 = temp_174.x;
    temp_176 = sysNormalAttr.x;
    temp_177 = sysNormalAttr.y;
    temp_178 = sysNormalAttr.z;
    temp_179 = sysTexCoordAttr.x;
    temp_180 = int(trunc(sysEmitterStaticUniformBlock.data[77].z));
    temp_181 = sysTexCoordAttr.y;
    temp_182 = int(trunc(sysEmitterStaticUniformBlock.data[82].z));
    temp_183 = temp_112 >= sysEmitterStaticUniformBlock.data[128].w ? 1.0 : 0.0;
    temp_184 = temp_112 >= sysEmitterStaticUniformBlock.data[129].w ? 1.0 : 0.0;
    temp_185 = ((!((1 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 1) || !(temp_50 > 0.5) ? -1 : 0)) != 0;
    temp_186 = fma(temp_183, (0.0 - temp_184), temp_183);
    temp_187 = (8 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 8;
    temp_188 = fma(fma((sysEmitterStaticUniformBlock.data[129].x + (0.0 - sysEmitterStaticUniformBlock.data[128].x)) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[128].w) + sysEmitterStaticUniformBlock.data[129].w)), temp_112 + (0.0 - sysEmitterStaticUniformBlock.data[128].w), sysEmitterStaticUniformBlock.data[128].x), temp_186, fma(temp_183, (0.0 - sysEmitterStaticUniformBlock.data[128].x), sysEmitterStaticUniformBlock.data[128].x));
    temp_189 = 0;
    temp_190 = temp_179;
    temp_191 = temp_181;
    temp_192 = intBitsToFloat((temp_187 ? -1 : 0));
    temp_193 = temp_186;
    temp_194 = temp_188;
    if ((1 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].z)) != 1)
    {
        temp_189 = 1;
    }
    temp_195 = temp_189;
    temp_196 = sysTangentAttr.z;
    temp_197 = floatBitsToInt(1.0 / float(uint(abs(temp_180)))) + -2;
    temp_198 = sysTangentAttr.x;
    temp_199 = floatBitsToInt(1.0 / float(uint(temp_180))) + -2;
    temp_200 = sysTangentAttr.y;
    temp_201 = temp_179;
    if (!temp_185)
    {
        temp_201 = (0.0 - temp_179) + 1.0;
    }
    temp_202 = floatBitsToInt(1.0 / float(uint(temp_182))) + -2;
    temp_203 = floatBitsToInt(1.0 / float(uint(abs(temp_182)))) + -2;
    temp_204 = uint(max(trunc(float(0u) * intBitsToFloat(temp_199)), 0.0));
    if (!(((!((4 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 4) || !(temp_114 > 0.5) ? -1 : 0)) != 0))
    {
        temp_190 = (0.0 - temp_179) + 1.0;
    }
    temp_205 = temp_121 == 0.0 && temp_122 == 0.0 && temp_123 == 0.0;
    temp_206 = temp_195 == 1;
    temp_207 = uint(max(trunc(float(0u) * intBitsToFloat(temp_202)), 0.0));
    temp_208 = uint(max(trunc(intBitsToFloat(temp_197) * float(0u)), 0.0));
    temp_209 = uint(max(trunc(float(0u) * intBitsToFloat(temp_203)), 0.0));
    temp_210 = temp_181;
    if (!(((!((2 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 2) || !(temp_113 > 0.5) ? -1 : 0)) != 0))
    {
        temp_210 = (0.0 - temp_181) + 1.0;
    }
    temp_211 = temp_50;
    temp_212 = temp_113;
    temp_213 = temp_50;
    temp_214 = temp_113;
    if (!(((!temp_187 || !(sysRandomAttr.w > 0.5) ? -1 : 0)) != 0))
    {
        temp_191 = (0.0 - temp_181) + 1.0;
    }
    if (temp_205)
    {
        temp_192 = temp_176;
    }
    temp_215 = temp_192;
    if (temp_205)
    {
        temp_193 = temp_177;
    }
    temp_216 = temp_193;
    if (temp_205)
    {
        temp_194 = temp_178;
    }
    temp_217 = temp_194;
    if (temp_206)
    {
        temp_211 = temp_113;
    }
    temp_218 = temp_211;
    temp_219 = temp_218;
    temp_220 = temp_218;
    if (temp_206)
    {
        temp_212 = temp_114;
    }
    temp_221 = temp_212;
    temp_222 = temp_221;
    temp_223 = temp_221;
    if (temp_206)
    {
        temp_213 = temp_113;
    }
    temp_224 = temp_213;
    temp_225 = temp_224;
    temp_226 = temp_224;
    if (temp_206)
    {
        temp_214 = temp_114;
    }
    temp_227 = temp_214;
    if (!temp_206)
    {
        temp_228 = temp_195 == 2;
        if (temp_228)
        {
            temp_219 = temp_114;
        }
        temp_220 = temp_219;
        if (temp_228)
        {
            temp_222 = temp_50;
        }
        temp_223 = temp_222;
        if (temp_228)
        {
            temp_225 = temp_50;
        }
        temp_226 = temp_225;
        if (temp_228)
        {
            temp_227 = temp_113;
        }
    }
    out_attr11.x = temp_163;
    if (!temp_205)
    {
        temp_215 = fma(temp_122, sysEmitterStaticUniformBlock.data[14].y, temp_176);
    }
    temp_229 = temp_215;
    out_attr11.y = temp_164;
    out_attr11.z = temp_167;
    out_attr5.x = temp_170;
    out_attr5.y = temp_171;
    if (!temp_205)
    {
        temp_217 = fma(temp_121, sysEmitterStaticUniformBlock.data[14].y, temp_178);
    }
    temp_230 = temp_217;
    out_attr5.z = temp_172;
    if (!temp_205)
    {
        temp_216 = fma(temp_123, sysEmitterStaticUniformBlock.data[14].y, temp_177);
    }
    temp_231 = temp_216;
    temp_232 = sysTangentAttr.w;
    temp_233 = fma(temp_167, NnVfx2ViewParam.data[10].z, fma(temp_164, NnVfx2ViewParam.data[10].y, temp_163 * NnVfx2ViewParam.data[10].x)) + NnVfx2ViewParam.data[10].w;
    temp_234 = int(temp_204) + int(uint(max(trunc(intBitsToFloat(temp_199) * float(uint((0 - temp_180 * int(temp_204))))), 0.0)));
    temp_235 = fma(temp_167, NnVfx2ViewParam.data[11].z, fma(temp_164, NnVfx2ViewParam.data[11].y, temp_163 * NnVfx2ViewParam.data[11].x)) + NnVfx2ViewParam.data[11].w;
    temp_236 = int(temp_207) + int(uint(max(trunc(intBitsToFloat(temp_202) * float(uint((0 - temp_182 * int(temp_207))))), 0.0)));
    temp_237 = int(temp_208) + int(uint(max(trunc(intBitsToFloat(temp_197) * float(uint((0 - abs(temp_180) * int(temp_208))))), 0.0)));
    temp_238 = fma(temp_177, temp_196, (0.0 - temp_178 * temp_200)) * temp_232;
    temp_239 = 1.0 / fma(0.0, temp_233, temp_235);
    temp_240 = fma(temp_233, 0.5, temp_235 * 0.5);
    temp_241 = fma(temp_178, temp_198, (0.0 - temp_176 * temp_196)) * temp_232;
    temp_242 = fma(temp_176, temp_200, (0.0 - temp_177 * temp_198)) * temp_232;
    temp_243 = int(temp_209) + int(uint(max(trunc(intBitsToFloat(temp_203) * float(uint((0 - abs(temp_182) * int(temp_209))))), 0.0)));
    temp_244 = 0.0 + fma(temp_157, (0.0 - temp_200), fma(temp_160, temp_198, temp_158 * temp_196));
    temp_245 = 0.0 + fma(temp_157, (0.0 - temp_231), fma(temp_160, temp_229, temp_158 * temp_230));
    temp_246 = 0.0 + fma(temp_157, (0.0 - temp_241), fma(temp_160, temp_238, temp_158 * temp_242));
    temp_247 = 0.0 + fma(sin(temp_148), temp_200, fma(temp_156, temp_198, temp_155 * temp_196));
    temp_248 = 0.0 + fma(sin(temp_148), temp_231, fma(temp_156, temp_229, temp_155 * temp_230));
    temp_249 = (0 - int(uint(temp_182) >> 31));
    temp_250 = 0.0 + fma(sin(temp_148), temp_241, fma(temp_156, temp_238, temp_155 * temp_242));
    temp_251 = 0.0 + fma(temp_162, (0.0 - temp_231), fma(temp_159, temp_229, temp_161 * temp_230));
    temp_252 = 0.0 + fma(temp_162, (0.0 - temp_241), fma(temp_159, temp_238, temp_161 * temp_242));
    temp_253 = 0.0 + fma(temp_162, (0.0 - temp_200), fma(temp_159, temp_198, temp_161 * temp_196));
    temp_254 = 1.0 / sysEmitterStaticUniformBlock.data[77].z * sysEmitterStaticUniformBlock.data[77].x;
    temp_255 = 1.0 / sysEmitterStaticUniformBlock.data[82].w * sysEmitterStaticUniformBlock.data[82].y;
    temp_256 = (0 - int(uint(temp_180) >> 31));
    temp_257 = 1.0 / sysEmitterStaticUniformBlock.data[82].z * sysEmitterStaticUniformBlock.data[82].x;
    out_attr7.z = fma(0.0, temp_167, fma(temp_253, temp_75, fma(temp_247, temp_72, temp_244 * temp_73)));
    out_attr4.x = sysVertexColor0Attr.x;
    temp_258 = fma(temp_172, NnVfx2ViewParam.data[0].z, fma(temp_171, NnVfx2ViewParam.data[0].y, temp_170 * NnVfx2ViewParam.data[0].x)) + NnVfx2ViewParam.data[0].w;
    out_attr1.w = fma(temp_184, sysEmitterStaticUniformBlock.data[129].x, temp_188) * NnVfx2EmitterDynamicParam.data[1].w;
    temp_259 = fma(temp_172, NnVfx2ViewParam.data[2].z, fma(temp_171, NnVfx2ViewParam.data[2].y, temp_170 * NnVfx2ViewParam.data[2].x)) + NnVfx2ViewParam.data[2].w;
    out_attr7.x = fma(0.0, temp_163, fma(temp_253, temp_67, fma(temp_247, temp_64, temp_244 * temp_63)));
    temp_260 = fma(temp_172, NnVfx2ViewParam.data[1].z, fma(temp_171, NnVfx2ViewParam.data[1].y, temp_170 * NnVfx2ViewParam.data[1].x)) + NnVfx2ViewParam.data[1].w;
    out_attr7.y = fma(0.0, temp_164, fma(temp_253, temp_58, fma(temp_247, temp_54, temp_244 * temp_55)));
    out_attr6.z = fma(0.0, temp_167, fma(temp_251, temp_75, fma(temp_248, temp_72, temp_245 * temp_73)));
    temp_261 = temp_259 + sysEmitterStaticUniformBlock.data[15].w;
    temp_262 = fma(temp_260, NnVfx2ViewParam.data[7].y, temp_258 * NnVfx2ViewParam.data[7].x);
    temp_263 = fma(temp_172, NnVfx2ViewParam.data[3].z, fma(temp_171, NnVfx2ViewParam.data[3].y, temp_170 * NnVfx2ViewParam.data[3].x)) + NnVfx2ViewParam.data[3].w;
    out_attr6.y = fma(0.0, temp_164, fma(temp_251, temp_58, fma(temp_248, temp_54, temp_245 * temp_55)));
    temp_264 = 1.0 / sysEmitterStaticUniformBlock.data[77].w * sysEmitterStaticUniformBlock.data[77].y;
    out_attr6.x = fma(0.0, temp_163, fma(temp_251, temp_67, fma(temp_248, temp_64, temp_245 * temp_63)));
    temp_265 = sysVertexColor0Attr.y;
    out_attr2.w = fma(fma(temp_1, sysEmitterStaticUniformBlock.data[79].w, fma(temp_227, sysEmitterStaticUniformBlock.data[80].w, sysEmitterStaticUniformBlock.data[80].w + sysEmitterStaticUniformBlock.data[80].y)), fma(temp_255, temp_191, -0.5), (0.0 - fma(temp_255, (0.0 - float(temp_182 < 0 || !(temp_182 == 0) ? (0 - temp_249) + (temp_243 + (0 - (uint((0 - abs(temp_182) * temp_243)) >= uint(abs(temp_182)) ? -1 : 0)) ^ temp_249) : -1)), fma(temp_1, sysEmitterStaticUniformBlock.data[78].y, fma(temp_223 * sysEmitterStaticUniformBlock.data[79].y, -2.0, sysEmitterStaticUniformBlock.data[79].y + sysEmitterStaticUniformBlock.data[78].w))))) + 0.5;
    temp_266 = fma(temp_263, NnVfx2ViewParam.data[7].w, fma(temp_259, NnVfx2ViewParam.data[7].z, temp_262));
    gl_Position.w = temp_266;
    out_attr4.y = temp_265;
    temp_267 = temp_266 * fma(temp_263, NnVfx2ViewParam.data[6].w, fma(temp_261, NnVfx2ViewParam.data[6].z, fma(temp_260, NnVfx2ViewParam.data[6].y, temp_258 * NnVfx2ViewParam.data[6].x))) * (1.0 / fma(temp_263, NnVfx2ViewParam.data[7].w, fma(temp_261, NnVfx2ViewParam.data[7].z, temp_262)));
    out_attr4.w = sysVertexColor0Attr.w;
    gl_Position.z = temp_267;
    out_attr2.y = fma(fma(temp_1, sysEmitterStaticUniformBlock.data[74].w, fma(temp_113, sysEmitterStaticUniformBlock.data[75].w, sysEmitterStaticUniformBlock.data[75].w + sysEmitterStaticUniformBlock.data[75].y)), fma(temp_264, temp_210, -0.5), (0.0 - fma(temp_264, (0.0 - float(temp_180 < 0 || !(temp_180 == 0) ? (0 - temp_256) + (temp_237 + (0 - (uint((0 - abs(temp_180) * temp_237)) >= uint(abs(temp_180)) ? -1 : 0)) ^ temp_256) : -1)), fma(temp_1, sysEmitterStaticUniformBlock.data[73].y, fma(temp_113 * sysEmitterStaticUniformBlock.data[74].y, -2.0, sysEmitterStaticUniformBlock.data[74].y + sysEmitterStaticUniformBlock.data[73].w))))) + 0.5;
    out_attr2.x = fma(fma(temp_254, temp_201, -0.5), fma(temp_1, sysEmitterStaticUniformBlock.data[74].z, fma(temp_50, sysEmitterStaticUniformBlock.data[75].z, sysEmitterStaticUniformBlock.data[75].x + sysEmitterStaticUniformBlock.data[75].z)), fma(temp_254, float(temp_180 < 0 || !(temp_180 == 0) ? (0 - temp_180 * (temp_234 + (0 - (uint((0 - temp_180 * temp_234)) >= uint(temp_180) ? -1 : 0)))) : -1), fma(temp_1, (0.0 - sysEmitterStaticUniformBlock.data[73].x), (0.0 - fma(temp_50 * sysEmitterStaticUniformBlock.data[74].x, -2.0, sysEmitterStaticUniformBlock.data[74].x + sysEmitterStaticUniformBlock.data[73].z))))) + 0.5;
    temp_268 = clamp(fma(temp_172, sysCustomShaderUniformBlock0.data[4].z, fma(temp_171, sysCustomShaderUniformBlock0.data[4].y, temp_170 * sysCustomShaderUniformBlock0.data[4].x)) + sysCustomShaderUniformBlock0.data[4].w, 0.0, 1.0);
    out_attr4.z = sysVertexColor0Attr.z;
    gl_Position.y = fma(temp_263, NnVfx2ViewParam.data[5].w, fma(temp_259, NnVfx2ViewParam.data[5].z, fma(temp_260, NnVfx2ViewParam.data[5].y, temp_258 * NnVfx2ViewParam.data[5].x)));
    temp_269 = fma(temp_175, (0.0 - temp_175), temp_174.y);
    gl_Position.x = fma(temp_263, NnVfx2ViewParam.data[4].w, fma(temp_259, NnVfx2ViewParam.data[4].z, fma(temp_260, NnVfx2ViewParam.data[4].y, temp_258 * NnVfx2ViewParam.data[4].x)));
    out_attr2.z = fma(fma(temp_1, sysEmitterStaticUniformBlock.data[79].z, fma(temp_226, sysEmitterStaticUniformBlock.data[80].z, sysEmitterStaticUniformBlock.data[80].x + sysEmitterStaticUniformBlock.data[80].z)), fma(temp_257, temp_190, -0.5), fma(temp_257, float(temp_182 < 0 || !(temp_182 == 0) ? (0 - temp_182 * (temp_236 + (0 - (uint((0 - temp_182 * temp_236)) >= uint(temp_182) ? -1 : 0)))) : -1), fma(temp_1, (0.0 - sysEmitterStaticUniformBlock.data[78].x), (0.0 - fma(temp_220 * sysEmitterStaticUniformBlock.data[79].x, -2.0, sysEmitterStaticUniformBlock.data[79].x + sysEmitterStaticUniformBlock.data[78].z))))) + 0.5;
    temp_270 = fma(temp_239 * (temp_240 + (0.0 - fma(temp_240 * sysEmitterStaticUniformBlock.data[15].w, (0.0 - temp_239), sysEmitterStaticUniformBlock.data[15].w))), NnVfx2ViewParam.data[30].w, (0.0 - NnVfx2ViewParam.data[30].y));
    temp_271 = sysCustomShaderUniformBlock0.data[18].w <= 1.0;
    out_attr8.z = fma(0.0, temp_167, fma(temp_252, temp_75, fma(temp_250, temp_72, temp_246 * temp_73)));
    out_attr8.y = fma(0.0, temp_164, fma(temp_252, temp_58, fma(temp_250, temp_54, temp_246 * temp_55)));
    out_attr8.x = fma(0.0, temp_163, fma(temp_252, temp_67, fma(temp_250, temp_64, temp_246 * temp_63)));
    temp_272 = min(temp_269 * (1.0 / fma((0.0 - temp_175) + temp_268, (0.0 - temp_175) + temp_268, temp_269)), 1.0);
    temp_273 = clamp(fma(1.0 / temp_270, (0.0 - NnVfx2ViewParam.data[30].z), (0.0 - sysEmitterStaticUniformBlock.data[137].x)) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[137].x) + sysEmitterStaticUniformBlock.data[137].y)), 0.0, 1.0);
    temp_274 = temp_272;
    temp_275 = temp_270;
    temp_276 = temp_265;
    if (temp_271)
    {
        temp_274 = 0.0;
    }
    out_attr3.x = temp_273 * NnVfx2EmitterDynamicParam.data[3].x;
    temp_277 = temp_274;
    if (!temp_271)
    {
        temp_278 = 1.0 / fma(fma(temp_267, 0.5, temp_266 * 0.5) * (1.0 / fma(0.0, temp_267, temp_266)), NnVfx2ViewParam.data[30].w, (0.0 - NnVfx2ViewParam.data[30].y)) * (0.0 - NnVfx2ViewParam.data[30].z);
        if (sysCustomShaderUniformBlock0.data[18].w == 2.0)
        {
            temp_277 = float(abs((temp_278 > sysCustomShaderUniformBlock0.data[18].x ? -1 : 0)) + abs((temp_278 > sysCustomShaderUniformBlock0.data[18].y ? -1 : 0)));
        }
        else
        {
            temp_277 = float(abs((temp_278 > sysCustomShaderUniformBlock0.data[18].z ? -1 : 0)) + abs((temp_278 > sysCustomShaderUniformBlock0.data[18].x ? -1 : 0)) + abs((temp_278 > sysCustomShaderUniformBlock0.data[18].y ? -1 : 0)));
        }
    }
    temp_279 = temp_277;
    if (temp_279 == 0.0)
    {
        temp_280 = fma(temp_172, sysCustomShaderUniformBlock0.data[6].z, fma(temp_171, sysCustomShaderUniformBlock0.data[6].y, temp_170 * sysCustomShaderUniformBlock0.data[6].x));
        temp_281 = fma(temp_172, sysCustomShaderUniformBlock0.data[9].z, fma(temp_171, sysCustomShaderUniformBlock0.data[9].y, temp_170 * sysCustomShaderUniformBlock0.data[9].x)) + sysCustomShaderUniformBlock0.data[9].w;
        temp_282 = fma(temp_172, sysCustomShaderUniformBlock0.data[8].z, fma(temp_171, sysCustomShaderUniformBlock0.data[8].y, temp_170 * sysCustomShaderUniformBlock0.data[8].x)) + sysCustomShaderUniformBlock0.data[8].w;
        temp_283 = temp_280 + sysCustomShaderUniformBlock0.data[6].w;
        temp_284 = fma(temp_172, sysCustomShaderUniformBlock0.data[7].z, fma(temp_171, sysCustomShaderUniformBlock0.data[7].y, temp_170 * sysCustomShaderUniformBlock0.data[7].x)) + sysCustomShaderUniformBlock0.data[7].w;
        temp_285 = temp_280;
    }
    else if (temp_279 == 1.0)
    {
        temp_286 = fma(temp_172, sysCustomShaderUniformBlock0.data[10].z, fma(temp_171, sysCustomShaderUniformBlock0.data[10].y, temp_170 * sysCustomShaderUniformBlock0.data[10].x));
        temp_281 = fma(temp_172, sysCustomShaderUniformBlock0.data[13].z, fma(temp_171, sysCustomShaderUniformBlock0.data[13].y, temp_170 * sysCustomShaderUniformBlock0.data[13].x)) + sysCustomShaderUniformBlock0.data[13].w;
        temp_282 = fma(temp_172, sysCustomShaderUniformBlock0.data[12].z, fma(temp_171, sysCustomShaderUniformBlock0.data[12].y, temp_170 * sysCustomShaderUniformBlock0.data[12].x)) + sysCustomShaderUniformBlock0.data[12].w;
        temp_283 = temp_286 + sysCustomShaderUniformBlock0.data[10].w;
        temp_284 = fma(temp_172, sysCustomShaderUniformBlock0.data[11].z, fma(temp_171, sysCustomShaderUniformBlock0.data[11].y, temp_170 * sysCustomShaderUniformBlock0.data[11].x)) + sysCustomShaderUniformBlock0.data[11].w;
        temp_285 = temp_286;
    }
    else
    {
        temp_287 = fma(temp_172, sysCustomShaderUniformBlock0.data[14].z, fma(temp_171, sysCustomShaderUniformBlock0.data[14].y, temp_170 * sysCustomShaderUniformBlock0.data[14].x));
        temp_281 = fma(temp_172, sysCustomShaderUniformBlock0.data[17].z, fma(temp_171, sysCustomShaderUniformBlock0.data[17].y, temp_170 * sysCustomShaderUniformBlock0.data[17].x)) + sysCustomShaderUniformBlock0.data[17].w;
        temp_282 = fma(temp_172, sysCustomShaderUniformBlock0.data[16].z, fma(temp_171, sysCustomShaderUniformBlock0.data[16].y, temp_170 * sysCustomShaderUniformBlock0.data[16].x)) + sysCustomShaderUniformBlock0.data[16].w;
        temp_283 = temp_287 + sysCustomShaderUniformBlock0.data[14].w;
        temp_284 = fma(temp_172, sysCustomShaderUniformBlock0.data[15].z, fma(temp_171, sysCustomShaderUniformBlock0.data[15].y, temp_170 * sysCustomShaderUniformBlock0.data[15].x)) + sysCustomShaderUniformBlock0.data[15].w;
        temp_285 = temp_287;
    }
    temp_288 = temp_281;
    temp_289 = temp_282;
    temp_290 = 0.0 == sysCustomShaderUniformBlock0.data[18].w;
    temp_291 = 1.0 / temp_288;
    temp_292 = temp_291 * temp_289;
    temp_293 = temp_291 * temp_283;
    temp_294 = temp_291 * temp_284;
    temp_295 = temp_285;
    temp_296 = temp_289;
    if (!temp_290)
    {
        temp_295 = temp_279;
    }
    temp_297 = temp_295;
    if (temp_290)
    {
        temp_297 = temp_292;
    }
    temp_298 = temp_297;
    if (temp_290)
    {
        temp_275 = texture(sysCustomShaderShadowSampler0, vec3(temp_293, temp_294, temp_298));
    }
    temp_299 = temp_275;
    if (!temp_290)
    {
        temp_296 = uintBitsToFloat(clamp(uint(max(roundEven(temp_298), 0.0)), 0u, 0xFFFFu));
    }
    if (temp_290)
    {
        temp_276 = temp_291 * temp_288;
    }
    temp_300 = temp_276;
    if (!temp_290)
    {
        temp_300 = temp_292;
    }
    if (!temp_290)
    {
        temp_299 = texture(sysCustomShaderShadowArraySampler0, vec4(temp_293, temp_294, float(floatBitsToInt(temp_296)), temp_300));
    }
    temp_301 = inversesqrt(fma(temp_259, temp_259, fma(temp_260, temp_260, temp_258 * temp_258)));
    out_attr14.x = temp_258 * temp_301;
    out_attr14.y = temp_260 * temp_301;
    if (0.0 < sysCustomShaderUniformBlock1.data[4].w)
    {
        temp_302 = (0.0 - temp_163) + temp_170;
        temp_303 = (0.0 - temp_164) + temp_171;
        temp_304 = (0.0 - temp_167) + temp_172;
        out_attr13.x = fma(fma(temp_304, NnVfx2ViewParam.data[0].z, fma(temp_303, NnVfx2ViewParam.data[0].y, temp_302 * NnVfx2ViewParam.data[0].x)), sysCustomShaderUniformBlock0.data[31].x, 0.5) * sysCustomShaderUniformBlock0.data[41].x;
        out_attr13.y = fma(fma(temp_304, NnVfx2ViewParam.data[1].z, fma(temp_303, NnVfx2ViewParam.data[1].y, temp_302 * NnVfx2ViewParam.data[1].x)), (0.0 - sysCustomShaderUniformBlock0.data[31].y), 0.5) * sysCustomShaderUniformBlock0.data[41].x;
    }
    out_attr14.z = temp_259 * temp_301;
    out_attr9.x = (0.0 - fma(temp_172, sysCustomShaderUniformBlock0.data[38].z, fma(temp_171, sysCustomShaderUniformBlock0.data[38].y, temp_170 * sysCustomShaderUniformBlock0.data[38].x))) + -0.0;
    out_attr10.x = sysCustomShaderUniformBlock0.data[36].w;
    out_attr12.x = clamp(0.0 + (0.0 - fma(texture(sysCustomShaderTextureSampler2, vec2(fma(temp_172, sysCustomShaderUniformBlock0.data[19].z, fma(temp_171, sysCustomShaderUniformBlock0.data[19].y, temp_170 * sysCustomShaderUniformBlock0.data[19].x)) + sysCustomShaderUniformBlock0.data[19].w, fma(temp_172, sysCustomShaderUniformBlock0.data[20].z, fma(temp_171, sysCustomShaderUniformBlock0.data[20].y, temp_170 * sysCustomShaderUniformBlock0.data[20].x)) + sysCustomShaderUniformBlock0.data[20].w)).x, (0.0 - sysCustomShaderUniformBlock0.data[22].x), sysCustomShaderUniformBlock0.data[22].x) + (0.0 - max(temp_272, temp_268 <= temp_175 ? 1.0 : 0.0)) + 1.0 + (0.0 - temp_299)), 0.0, 1.0);
    if (!(temp_273 <= 0.0))
    {
        return;
    }
    gl_Position.x = 0.0;
    gl_Position.y = 0.0;
    gl_Position.z = NnVfx2ViewParam.data[30].y * 5.0;
    out_attr3.x = 0.0;
    return;
}
