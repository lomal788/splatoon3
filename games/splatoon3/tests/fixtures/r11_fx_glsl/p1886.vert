// static_grsn.bfsha model VfxGeneralShader program 1886 (vert)
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
    bool temp_21;
    bool temp_22;
    bool temp_23;
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
    int temp_116;
    precise float temp_117;
    precise float temp_118;
    bool temp_119;
    precise float temp_120;
    bool temp_121;
    precise float temp_122;
    int temp_123;
    bool temp_124;
    precise float temp_125;
    int temp_126;
    precise float temp_127;
    precise float temp_128;
    precise float temp_129;
    precise float temp_130;
    bool temp_131;
    precise float temp_132;
    precise float temp_133;
    precise float temp_134;
    precise float temp_135;
    int temp_136;
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
    bool temp_150;
    precise float temp_151;
    int temp_152;
    precise float temp_153;
    precise float temp_154;
    precise float temp_155;
    precise float temp_156;
    precise float temp_157;
    precise float temp_158;
    precise float temp_159;
    int temp_160;
    precise float temp_161;
    precise float temp_162;
    precise float temp_163;
    precise float temp_164;
    precise float temp_165;
    precise float temp_166;
    precise float temp_167;
    precise float temp_168;
    int temp_169;
    precise float temp_170;
    precise float temp_171;
    int temp_172;
    uint temp_173;
    precise float temp_174;
    int temp_175;
    precise float temp_176;
    bool temp_177;
    uint temp_178;
    bool temp_179;
    precise float temp_180;
    precise float temp_181;
    precise float temp_182;
    precise float temp_183;
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
    bool temp_197;
    int temp_198;
    int temp_199;
    precise float temp_200;
    precise float temp_201;
    uint temp_202;
    uint temp_203;
    precise float temp_204;
    precise float temp_205;
    precise float temp_206;
    precise float temp_207;
    precise float temp_208;
    precise float temp_209;
    precise float temp_210;
    precise float temp_211;
    precise float temp_212;
    precise float temp_213;
    precise float temp_214;
    precise float temp_215;
    precise float temp_216;
    int temp_217;
    int temp_218;
    precise float temp_219;
    precise float temp_220;
    precise float temp_221;
    precise float temp_222;
    precise float temp_223;
    precise float temp_224;
    precise float temp_225;
    precise float temp_226;
    int temp_227;
    precise float temp_228;
    precise float temp_229;
    precise float temp_230;
    precise float temp_231;
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
    int temp_246;
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
    int temp_263;
    precise float temp_264;
    precise float temp_265;
    precise float temp_266;
    precise float temp_267;
    precise float temp_268;
    precise float temp_269;
    precise float temp_270;
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
    temp_15 = sysEmtMat0Attr.z;
    temp_16 = sysEmtMat1Attr.z;
    temp_17 = sysEmtMat2Attr.z;
    temp_18 = fma(temp_15, temp_15, fma(temp_12, temp_12, temp_7 * temp_7));
    temp_19 = fma(temp_16, temp_16, fma(temp_13, temp_13, temp_9 * temp_9));
    temp_20 = fma(temp_17, temp_17, fma(temp_14, temp_14, temp_11 * temp_11));
    temp_21 = sqrt(temp_18) > 0.0;
    temp_22 = sqrt(temp_19) > 0.0;
    temp_23 = sqrt(temp_20) > 0.0;
    temp_24 = sqrt(temp_20);
    temp_25 = temp_19;
    temp_26 = temp_20;
    temp_27 = temp_18;
    temp_28 = temp_8;
    if (temp_10)
    {
        temp_24 = temp_8 * temp_8;
    }
    temp_29 = temp_24;
    temp_30 = intBitsToFloat(undef);
    temp_31 = temp_29;
    if (temp_21)
    {
        temp_30 = inversesqrt(temp_18);
    }
    temp_32 = temp_30;
    if (temp_10)
    {
        temp_31 = temp_29 * sysEmitterStaticUniformBlock.data[13].w;
    }
    temp_33 = temp_31;
    temp_34 = sysScaleAttr.w;
    temp_35 = intBitsToFloat(undef);
    if (temp_10)
    {
        temp_35 = temp_33 * 0.5 * sysEmitterStaticUniformBlock.data[13].y;
    }
    temp_36 = intBitsToFloat(undef);
    temp_37 = temp_35;
    if (temp_22)
    {
        temp_36 = inversesqrt(temp_19);
    }
    temp_38 = temp_36;
    temp_39 = intBitsToFloat(undef);
    if (temp_10)
    {
        temp_39 = temp_33 * 0.5 * sysEmitterStaticUniformBlock.data[13].z;
    }
    temp_40 = intBitsToFloat(undef);
    temp_41 = temp_39;
    if (temp_23)
    {
        temp_40 = inversesqrt(temp_20);
    }
    temp_42 = temp_40;
    temp_43 = intBitsToFloat(undef);
    if (temp_10)
    {
        temp_43 = temp_33 * 0.5 * sysEmitterStaticUniformBlock.data[13].x;
    }
    temp_44 = temp_43;
    temp_45 = intBitsToFloat(undef);
    if (!temp_10)
    {
        temp_46 = temp_8 * log2(abs(sysEmitterStaticUniformBlock.data[14].x));
        temp_47 = 1.0 / log2(sysEmitterStaticUniformBlock.data[14].x);
        temp_48 = temp_47 * 1.44269502;
        temp_49 = (temp_8 + (0.0 - fma(temp_48, exp2(temp_46), (0.0 - temp_48)))) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[14].x) + 1.0)) * sysEmitterStaticUniformBlock.data[13].w;
        temp_37 = temp_49 * sysEmitterStaticUniformBlock.data[13].y;
        temp_25 = temp_47;
        temp_44 = temp_49 * sysEmitterStaticUniformBlock.data[13].x;
        temp_45 = temp_46;
        temp_41 = temp_49 * sysEmitterStaticUniformBlock.data[13].z;
        temp_26 = temp_49;
        temp_27 = temp_48;
    }
    temp_50 = temp_37;
    temp_51 = temp_44;
    temp_52 = temp_41;
    temp_53 = temp_25;
    temp_54 = temp_45;
    temp_55 = temp_26;
    temp_56 = temp_27;
    if (temp_22)
    {
        temp_53 = temp_38 * temp_13;
    }
    temp_57 = sysRandomAttr.x;
    temp_58 = temp_53;
    if (!temp_22)
    {
        temp_58 = 0.0;
    }
    temp_59 = temp_58;
    temp_60 = intBitsToFloat(undef);
    if (temp_23)
    {
        temp_60 = temp_42 * temp_16;
    }
    temp_61 = intBitsToFloat(undef);
    temp_62 = temp_60;
    if (temp_21)
    {
        temp_61 = temp_32 * temp_9;
    }
    temp_63 = temp_61;
    if (!temp_23)
    {
        temp_62 = 0.0;
    }
    temp_64 = temp_62;
    if (!temp_21)
    {
        temp_63 = 0.0;
    }
    temp_65 = temp_63;
    if (temp_22)
    {
        temp_54 = temp_38 * temp_12;
    }
    temp_66 = temp_54;
    if (!temp_22)
    {
        temp_66 = 0.0;
    }
    temp_67 = temp_66;
    temp_68 = intBitsToFloat(undef);
    if (temp_21)
    {
        temp_68 = temp_32 * temp_7;
    }
    temp_69 = intBitsToFloat(undef);
    temp_70 = temp_68;
    if (temp_23)
    {
        temp_69 = temp_42 * temp_15;
    }
    temp_71 = temp_69;
    if (!temp_21)
    {
        temp_70 = 0.0;
    }
    temp_72 = temp_70;
    if (!temp_23)
    {
        temp_71 = 0.0;
    }
    temp_73 = temp_71;
    temp_74 = intBitsToFloat(undef);
    if (temp_22)
    {
        temp_74 = temp_38 * temp_14;
    }
    temp_75 = temp_74;
    if (!temp_22)
    {
        temp_75 = 0.0;
    }
    temp_76 = temp_75;
    if (temp_21)
    {
        temp_55 = temp_32 * temp_11;
    }
    temp_77 = temp_55;
    if (temp_23)
    {
        temp_56 = temp_42 * temp_17;
    }
    temp_78 = temp_56;
    if (!temp_21)
    {
        temp_77 = 0.0;
    }
    temp_79 = temp_77;
    if (!temp_23)
    {
        temp_78 = 0.0;
    }
    temp_80 = temp_78;
    if (!temp_10)
    {
        temp_81 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[14].x) + 1.0);
        temp_28 = fma(exp2(temp_8 * log2(abs(sysEmitterStaticUniformBlock.data[14].x))), (0.0 - temp_81), temp_81);
    }
    temp_82 = temp_28;
    temp_83 = fma(fma(temp_82, sysLocalVecAttr.x, fma(temp_52, temp_79, fma(temp_51, temp_72, temp_50 * temp_65))), temp_34, sysLocalPosAttr.x);
    temp_84 = fma(fma(temp_82, sysLocalVecAttr.y, fma(temp_52, temp_76, fma(temp_51, temp_67, temp_50 * temp_59))), temp_34, sysLocalPosAttr.y);
    temp_85 = fma(fma(temp_82, sysLocalVecAttr.z, fma(temp_52, temp_80, fma(temp_51, temp_73, temp_50 * temp_64))), temp_34, sysLocalPosAttr.z);
    if (0.0 < sysEmitterStaticUniformBlock.data[11].x)
    {
        temp_86 = fma(temp_57 * sysEmitterStaticUniformBlock.data[12].y, sysEmitterStaticUniformBlock.data[11].x, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[11].x);
        temp_87 = temp_86 + (0.0 - floor(temp_86));
    }
    else
    {
        temp_87 = temp_1 * (1.0 / temp_2);
    }
    temp_88 = temp_87;
    temp_89 = 1.0 / (sysEmitterStaticUniformBlock.data[142].w + (0.0 - sysEmitterStaticUniformBlock.data[141].w));
    temp_90 = 1.0 / (sysEmitterStaticUniformBlock.data[141].w + (0.0 - sysEmitterStaticUniformBlock.data[140].w));
    temp_91 = temp_88 + (0.0 - sysEmitterStaticUniformBlock.data[141].w);
    temp_92 = temp_88 >= sysEmitterStaticUniformBlock.data[141].w ? 1.0 : 0.0;
    temp_93 = temp_88 >= sysEmitterStaticUniformBlock.data[140].w ? 1.0 : 0.0;
    temp_94 = temp_88 + (0.0 - sysEmitterStaticUniformBlock.data[140].w);
    temp_95 = temp_88 >= sysEmitterStaticUniformBlock.data[142].w ? 1.0 : 0.0;
    temp_96 = fma(temp_93, (0.0 - temp_92), temp_93);
    temp_97 = fma(temp_92, (0.0 - temp_95), temp_92);
    if (0.0 < sysEmitterStaticUniformBlock.data[10].y)
    {
        temp_98 = fma(temp_57 * sysEmitterStaticUniformBlock.data[11].z, sysEmitterStaticUniformBlock.data[10].y, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[10].y);
        temp_99 = temp_98 + (0.0 - floor(temp_98));
    }
    else
    {
        temp_99 = temp_1 * (1.0 / temp_2);
    }
    temp_100 = temp_99;
    temp_101 = temp_100 >= sysEmitterStaticUniformBlock.data[112].w ? 1.0 : 0.0;
    temp_102 = temp_100 >= sysEmitterStaticUniformBlock.data[113].w ? 1.0 : 0.0;
    out_attr0.x = sysEmitterStaticUniformBlock.data[104].x * NnVfx2EmitterDynamicParam.data[0].x * sysEmitterStaticUniformBlock.data[103].x;
    out_attr0.y = sysEmitterStaticUniformBlock.data[104].y * NnVfx2EmitterDynamicParam.data[0].y * sysEmitterStaticUniformBlock.data[103].x;
    out_attr0.z = sysEmitterStaticUniformBlock.data[104].z * NnVfx2EmitterDynamicParam.data[0].z * sysEmitterStaticUniformBlock.data[103].x;
    out_attr0.w = fma(temp_102, sysEmitterStaticUniformBlock.data[113].x, fma(fma((sysEmitterStaticUniformBlock.data[113].x + (0.0 - sysEmitterStaticUniformBlock.data[112].x)) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[112].w) + sysEmitterStaticUniformBlock.data[113].w)), temp_100 + (0.0 - sysEmitterStaticUniformBlock.data[112].w), sysEmitterStaticUniformBlock.data[112].x), fma(temp_101, (0.0 - temp_102), temp_101), fma(temp_101, (0.0 - sysEmitterStaticUniformBlock.data[112].x), sysEmitterStaticUniformBlock.data[112].x))) * NnVfx2EmitterDynamicParam.data[0].w;
    if (0.0 < sysEmitterStaticUniformBlock.data[10].z)
    {
        temp_103 = fma(temp_57 * sysEmitterStaticUniformBlock.data[11].w, sysEmitterStaticUniformBlock.data[10].z, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[10].z);
        temp_104 = temp_103 + (0.0 - floor(temp_103));
    }
    else
    {
        temp_104 = temp_1 * (1.0 / temp_2);
    }
    temp_105 = temp_104;
    temp_106 = sysRandomAttr.y;
    temp_107 = sysPosAttr.y;
    temp_108 = sysPosAttr.x;
    temp_109 = sysRandomAttr.z;
    temp_110 = sysPosAttr.z;
    temp_111 = sysTexCoordAttr.x;
    temp_112 = sysInitRotateAttr.y;
    temp_113 = sysNormalAttr.x;
    temp_114 = sysNormalAttr.y;
    temp_115 = sysInitRotateAttr.x;
    temp_116 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x20000000;
    temp_117 = fma(temp_95, sysEmitterStaticUniformBlock.data[142].y, fma(fma((sysEmitterStaticUniformBlock.data[142].y + (0.0 - sysEmitterStaticUniformBlock.data[141].y)) * temp_89, temp_91, sysEmitterStaticUniformBlock.data[141].y), temp_97, fma(fma(temp_94, (sysEmitterStaticUniformBlock.data[141].y + (0.0 - sysEmitterStaticUniformBlock.data[140].y)) * temp_90, sysEmitterStaticUniformBlock.data[140].y), temp_96, fma(temp_93, (0.0 - sysEmitterStaticUniformBlock.data[140].y), sysEmitterStaticUniformBlock.data[140].y)))) * sysScaleAttr.y * NnVfx2EmitterDynamicParam.data[3].z * fma(0.5, sysEmitterStaticUniformBlock.data[15].y, temp_107);
    temp_118 = (clamp(min(0.0, temp_57) + -0.0, 0.0, 1.0) + sysScaleAttr.x) * fma(temp_95, sysEmitterStaticUniformBlock.data[142].x, fma(fma((sysEmitterStaticUniformBlock.data[142].x + (0.0 - sysEmitterStaticUniformBlock.data[141].x)) * temp_89, temp_91, sysEmitterStaticUniformBlock.data[141].x), temp_97, fma(fma(temp_94, (sysEmitterStaticUniformBlock.data[141].x + (0.0 - sysEmitterStaticUniformBlock.data[140].x)) * temp_90, sysEmitterStaticUniformBlock.data[140].x), temp_96, fma(temp_93, (0.0 - sysEmitterStaticUniformBlock.data[140].x), sysEmitterStaticUniformBlock.data[140].x)))) * NnVfx2EmitterDynamicParam.data[3].y * fma(0.5, sysEmitterStaticUniformBlock.data[15].x, temp_108);
    temp_119 = ((!((4 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 4) || !(temp_109 > 0.5) ? -1 : 0)) != 0;
    temp_120 = floor(temp_57 * 2.0);
    temp_121 = sysRandomAttr.w > 0.5;
    temp_122 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[120].w) + sysEmitterStaticUniformBlock.data[121].w);
    temp_123 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x40000000;
    temp_124 = ((!((1 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 1) || !(temp_57 > 0.5) ? -1 : 0)) != 0;
    temp_125 = fma(temp_95, sysEmitterStaticUniformBlock.data[142].z, fma(fma((sysEmitterStaticUniformBlock.data[142].z + (0.0 - sysEmitterStaticUniformBlock.data[141].z)) * temp_89, temp_91, sysEmitterStaticUniformBlock.data[141].z), temp_97, fma(fma(temp_94, (sysEmitterStaticUniformBlock.data[141].z + (0.0 - sysEmitterStaticUniformBlock.data[140].z)) * temp_90, sysEmitterStaticUniformBlock.data[140].z), temp_96, fma(temp_93, (0.0 - sysEmitterStaticUniformBlock.data[140].z), sysEmitterStaticUniformBlock.data[140].z)))) * sysScaleAttr.z * NnVfx2EmitterDynamicParam.data[3].w * fma(0.5, sysEmitterStaticUniformBlock.data[15].z, temp_110);
    temp_126 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x10000000;
    temp_127 = sysTexCoordAttr.y;
    temp_128 = fma(temp_85, temp_17, fma(temp_84, temp_14, temp_83 * temp_11)) + sysEmtMat2Attr.w;
    temp_129 = fma(temp_85, temp_16, fma(temp_84, temp_13, temp_83 * temp_9)) + sysEmtMat1Attr.w;
    temp_130 = fma(temp_85, temp_15, fma(temp_84, temp_12, temp_83 * temp_7)) + sysEmtMat0Attr.w;
    temp_131 = 0.0 == sysEmitterStaticUniformBlock.data[162].w;
    temp_132 = (0.0 - temp_120 < 0.0 ? 1.0 : 0.0) + (temp_120 > 0.0 ? 1.0 : 0.0);
    temp_133 = temp_105 + (0.0 - sysEmitterStaticUniformBlock.data[120].w);
    temp_134 = float(abs((0 - (temp_126 > 0 ? -1 : 0)) + (0 - temp_126 >= 0 ? 0 : 1)));
    temp_135 = floor(temp_106 * 2.0);
    temp_136 = int(trunc(sysEmitterStaticUniformBlock.data[77].z));
    temp_137 = intBitsToFloat((temp_121 ? -1 : 0));
    temp_138 = temp_132;
    temp_139 = temp_134;
    if (!temp_131)
    {
        temp_137 = log2(abs(sysEmitterStaticUniformBlock.data[162].w));
    }
    temp_140 = temp_137;
    temp_141 = fma(fma(temp_57 + temp_109, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].z, 2.0, sysEmitterStaticUniformBlock.data[162].z);
    temp_142 = temp_105 >= sysEmitterStaticUniformBlock.data[120].w ? 1.0 : 0.0;
    temp_143 = temp_111;
    temp_144 = temp_111;
    temp_145 = temp_140;
    if (!temp_124)
    {
        temp_143 = (0.0 - temp_111) + 1.0;
    }
    if (!temp_119)
    {
        temp_144 = (0.0 - temp_111) + 1.0;
    }
    temp_146 = fma(fma(temp_57 + temp_106, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].x, 2.0, sysEmitterStaticUniformBlock.data[162].x);
    temp_147 = temp_105 >= sysEmitterStaticUniformBlock.data[121].w ? 1.0 : 0.0;
    temp_148 = fma(fma(temp_106 + temp_109, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].y, 2.0, sysEmitterStaticUniformBlock.data[162].y);
    temp_149 = floor(temp_109 * 2.0);
    temp_150 = sysEmitterStaticUniformBlock.data[162].w == 1.0;
    if (!temp_131)
    {
        temp_145 = temp_1 * temp_140;
    }
    temp_151 = temp_145;
    temp_152 = int(trunc(sysEmitterStaticUniformBlock.data[82].z));
    temp_153 = intBitsToFloat(undef);
    temp_154 = temp_151;
    if (!temp_131)
    {
        temp_153 = temp_151;
    }
    temp_155 = intBitsToFloat(undef);
    if (!temp_131)
    {
        temp_155 = exp2(temp_153);
    }
    temp_156 = temp_155;
    if (!temp_150)
    {
        temp_154 = (0.0 - sysEmitterStaticUniformBlock.data[162].w) + 1.0;
    }
    temp_157 = temp_154;
    temp_158 = fma(temp_142, (0.0 - temp_147), temp_142);
    temp_159 = temp_157;
    if (!temp_150)
    {
        temp_159 = 1.0 / temp_157;
    }
    temp_160 = floatBitsToInt(1.0 / float(uint(temp_136))) + -2;
    temp_161 = fma(fma(temp_133, (sysEmitterStaticUniformBlock.data[121].x + (0.0 - sysEmitterStaticUniformBlock.data[120].x)) * temp_122, sysEmitterStaticUniformBlock.data[120].x), temp_158, fma(temp_142, (0.0 - sysEmitterStaticUniformBlock.data[120].x), sysEmitterStaticUniformBlock.data[120].x));
    temp_162 = temp_127;
    temp_163 = temp_161;
    temp_164 = temp_127;
    if (!(((!((2 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 2) || !(temp_106 > 0.5) ? -1 : 0)) != 0))
    {
        temp_162 = (0.0 - temp_127) + 1.0;
    }
    temp_165 = sysNormalAttr.z;
    if (!(((!((8 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 8) || !temp_121 ? -1 : 0)) != 0))
    {
        temp_164 = (0.0 - temp_127) + 1.0;
    }
    temp_166 = temp_132 * float(abs((0 - (temp_116 > 0 ? -1 : 0)) + (0 - temp_116 >= 0 ? 0 : 1)));
    if (temp_131)
    {
        temp_156 = 1.0;
    }
    temp_167 = ((0.0 - temp_135 < 0.0 ? 1.0 : 0.0) + (temp_135 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_123 > 0 ? -1 : 0)) + (0 - temp_123 >= 0 ? 0 : 1)));
    temp_168 = intBitsToFloat(undef);
    temp_169 = 0;
    if (!temp_150)
    {
        temp_168 = fma(temp_159, (0.0 - temp_156), temp_159);
    }
    temp_170 = sysInitRotateAttr.z;
    temp_171 = ((0.0 - temp_149 < 0.0 ? 1.0 : 0.0) + (temp_149 > 0.0 ? 1.0 : 0.0)) * temp_134;
    temp_172 = floatBitsToInt(1.0 / float(uint(temp_152))) + -2;
    temp_173 = uint(max(trunc(float(0u) * intBitsToFloat(temp_160)), 0.0));
    temp_174 = temp_168;
    if ((1 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].z)) != 1)
    {
        temp_169 = 1;
    }
    temp_175 = temp_169;
    if (temp_150)
    {
        temp_174 = temp_1;
    }
    temp_176 = temp_174;
    temp_177 = temp_110 == 0.0 && temp_108 == 0.0 && temp_107 == 0.0;
    temp_178 = uint(max(trunc(float(0u) * intBitsToFloat(temp_172)), 0.0));
    temp_179 = temp_175 == 1;
    temp_180 = temp_57;
    temp_181 = temp_106;
    temp_182 = temp_57;
    if (temp_177)
    {
        temp_138 = temp_113;
    }
    temp_183 = temp_138;
    if (temp_177)
    {
        temp_139 = temp_114;
    }
    temp_184 = temp_139;
    if (temp_177)
    {
        temp_163 = temp_165;
    }
    temp_185 = temp_106;
    temp_186 = temp_163;
    if (temp_179)
    {
        temp_180 = temp_106;
    }
    temp_187 = temp_180;
    temp_188 = temp_187;
    temp_189 = temp_187;
    if (temp_179)
    {
        temp_181 = temp_109;
    }
    temp_190 = temp_181;
    temp_191 = temp_190;
    temp_192 = temp_190;
    if (temp_179)
    {
        temp_182 = temp_106;
    }
    temp_193 = temp_182;
    temp_194 = temp_193;
    temp_195 = temp_193;
    if (temp_179)
    {
        temp_185 = temp_109;
    }
    temp_196 = temp_185;
    if (!temp_179)
    {
        temp_197 = temp_175 == 2;
        if (temp_197)
        {
            temp_188 = temp_109;
        }
        temp_189 = temp_188;
        if (temp_197)
        {
            temp_191 = temp_57;
        }
        temp_192 = temp_191;
        if (temp_197)
        {
            temp_194 = temp_57;
        }
        temp_195 = temp_194;
        if (temp_197)
        {
            temp_196 = temp_106;
        }
    }
    temp_198 = floatBitsToInt(1.0 / float(uint(abs(temp_136)))) + -2;
    out_attr12.x = temp_130;
    temp_199 = floatBitsToInt(1.0 / float(uint(abs(temp_152)))) + -2;
    out_attr12.y = temp_129;
    if (!temp_177)
    {
        temp_183 = fma(temp_108, sysEmitterStaticUniformBlock.data[14].y, temp_113);
    }
    temp_200 = temp_183;
    temp_201 = sysTangentAttr.y;
    out_attr12.z = temp_128;
    temp_202 = uint(max(trunc(intBitsToFloat(temp_198) * float(0u)), 0.0));
    temp_203 = uint(max(trunc(float(0u) * intBitsToFloat(temp_199)), 0.0));
    if (!temp_177)
    {
        temp_186 = fma(temp_110, sysEmitterStaticUniformBlock.data[14].y, temp_165);
    }
    temp_204 = temp_186;
    temp_205 = sysTangentAttr.z;
    if (!temp_177)
    {
        temp_184 = fma(temp_107, sysEmitterStaticUniformBlock.data[14].y, temp_114);
    }
    temp_206 = temp_184;
    temp_207 = sysTangentAttr.x;
    temp_208 = sysTangentAttr.w;
    temp_209 = fma(fma(temp_148 * temp_166, -2.0, temp_148), temp_176, fma(temp_106 + -0.5, sysEmitterStaticUniformBlock.data[161].y, fma(temp_166 * temp_112, -2.0, temp_112)));
    temp_210 = fma(temp_128, NnVfx2ViewParam.data[11].z, fma(temp_129, NnVfx2ViewParam.data[11].y, temp_130 * NnVfx2ViewParam.data[11].x)) + NnVfx2ViewParam.data[11].w;
    temp_211 = fma(fma(temp_146 * temp_171, -2.0, temp_146), temp_176, fma(temp_57 + -0.5, sysEmitterStaticUniformBlock.data[161].x, fma(temp_171 * temp_115, -2.0, temp_115)));
    temp_212 = fma(temp_114, temp_205, (0.0 - temp_165 * temp_201)) * temp_208;
    temp_213 = fma(temp_128, NnVfx2ViewParam.data[10].z, fma(temp_129, NnVfx2ViewParam.data[10].y, temp_130 * NnVfx2ViewParam.data[10].x)) + NnVfx2ViewParam.data[10].w;
    temp_214 = fma(temp_165, temp_207, (0.0 - temp_113 * temp_205)) * temp_208;
    temp_215 = fma(temp_113, temp_201, (0.0 - temp_114 * temp_207)) * temp_208;
    temp_216 = fma(fma(temp_141 * temp_167, -2.0, temp_141), temp_176, fma(temp_109 + -0.5, sysEmitterStaticUniformBlock.data[161].z, fma(temp_167 * temp_170, -2.0, temp_170)));
    temp_217 = int(temp_173) + int(uint(max(trunc(intBitsToFloat(temp_160) * float(uint((0 - temp_136 * int(temp_173))))), 0.0)));
    temp_218 = int(temp_178) + int(uint(max(trunc(intBitsToFloat(temp_172) * float(uint((0 - temp_152 * int(temp_178))))), 0.0)));
    temp_219 = cos(temp_209) * sin(temp_216);
    temp_220 = cos(temp_209) * cos(temp_216);
    temp_221 = sin(temp_216) * cos(temp_211);
    temp_222 = cos(temp_209) * cos(temp_211);
    temp_223 = cos(temp_216) * cos(temp_211);
    temp_224 = sin(temp_216) * sin(temp_209);
    temp_225 = cos(temp_216) * sin(temp_209);
    temp_226 = sin(temp_209) * cos(temp_211);
    temp_227 = int(temp_203) + int(uint(max(trunc(intBitsToFloat(temp_199) * float(uint((0 - abs(temp_152) * int(temp_203))))), 0.0)));
    temp_228 = fma(sin(temp_211), temp_224, temp_220);
    temp_229 = fma(sin(temp_211), temp_219, (0.0 - temp_225));
    temp_230 = fma(sin(temp_211), temp_220, temp_224);
    temp_231 = fma(sin(temp_211), temp_225, (0.0 - temp_219));
    temp_232 = int(temp_202) + int(uint(max(trunc(intBitsToFloat(temp_198) * float(uint((0 - abs(temp_136) * int(temp_202))))), 0.0)));
    temp_233 = 0.0 + fma(temp_117, (0.0 - temp_226), fma(temp_228, temp_118, temp_231 * temp_125));
    temp_234 = 0.0 + fma(temp_226, (0.0 - temp_206), fma(temp_228, temp_200, temp_231 * temp_204));
    temp_235 = 0.0 + fma(temp_226, (0.0 - temp_201), fma(temp_228, temp_207, temp_231 * temp_205));
    temp_236 = 0.0 + fma(temp_226, (0.0 - temp_214), fma(temp_228, temp_212, temp_231 * temp_215));
    temp_237 = 0.0 + fma(sin(temp_211), temp_117, fma(temp_118, temp_221, temp_125 * temp_223));
    temp_238 = 0.0 + fma(sin(temp_211), temp_201, fma(temp_221, temp_207, temp_223 * temp_205));
    temp_239 = 0.0 + fma(sin(temp_211), temp_206, fma(temp_221, temp_200, temp_223 * temp_204));
    temp_240 = 0.0 + fma(sin(temp_211), temp_214, fma(temp_221, temp_212, temp_223 * temp_215));
    temp_241 = 0.0 + fma(temp_117, (0.0 - temp_222), fma(temp_229, temp_118, temp_230 * temp_125));
    temp_242 = 0.0 + fma(temp_222, (0.0 - temp_201), fma(temp_229, temp_207, temp_230 * temp_205));
    temp_243 = 0.0 + fma(temp_222, (0.0 - temp_206), fma(temp_229, temp_200, temp_230 * temp_204));
    temp_244 = fma(0.0, (0.0 - temp_117), fma(0.0, temp_118, 0.0 * temp_125)) + 1.0;
    temp_245 = 0.0 + fma(temp_222, (0.0 - temp_214), fma(temp_229, temp_212, temp_230 * temp_215));
    out_attr5.y = sysVertexColor0Attr.y;
    out_attr5.z = sysVertexColor0Attr.z;
    temp_246 = (0 - int(uint(temp_136) >> 31));
    out_attr5.x = sysVertexColor0Attr.x;
    temp_247 = fma(temp_130, temp_244, fma(temp_241, temp_73, fma(temp_237, temp_67, temp_233 * temp_72)));
    temp_248 = fma(temp_129, temp_244, fma(temp_241, temp_64, fma(temp_237, temp_59, temp_233 * temp_65)));
    out_attr6.x = temp_247;
    out_attr5.w = sysVertexColor0Attr.w;
    out_attr6.y = temp_248;
    temp_249 = 1.0 / sysEmitterStaticUniformBlock.data[77].w * sysEmitterStaticUniformBlock.data[77].y;
    temp_250 = fma(temp_128, temp_244, fma(temp_241, temp_80, fma(temp_237, temp_76, temp_233 * temp_79)));
    out_attr6.z = temp_250;
    out_attr1.w = sysEmitterStaticUniformBlock.data[128].x * NnVfx2EmitterDynamicParam.data[1].w;
    temp_251 = 1.0 / sysEmitterStaticUniformBlock.data[77].z * sysEmitterStaticUniformBlock.data[77].x;
    out_attr1.x = fma(temp_147, sysEmitterStaticUniformBlock.data[121].x, temp_161) * NnVfx2EmitterDynamicParam.data[1].x * sysEmitterStaticUniformBlock.data[103].x;
    temp_252 = 1.0 / sysEmitterStaticUniformBlock.data[82].w * sysEmitterStaticUniformBlock.data[82].y;
    out_attr1.y = fma(temp_147, sysEmitterStaticUniformBlock.data[121].y, fma(fma(temp_133, (sysEmitterStaticUniformBlock.data[121].y + (0.0 - sysEmitterStaticUniformBlock.data[120].y)) * temp_122, sysEmitterStaticUniformBlock.data[120].y), temp_158, fma(temp_142, (0.0 - sysEmitterStaticUniformBlock.data[120].y), sysEmitterStaticUniformBlock.data[120].y))) * NnVfx2EmitterDynamicParam.data[1].y * sysEmitterStaticUniformBlock.data[103].x;
    temp_253 = 1.0 / sysEmitterStaticUniformBlock.data[82].z * sysEmitterStaticUniformBlock.data[82].x;
    out_attr8.y = fma(0.0, temp_129, fma(temp_242, temp_64, fma(temp_238, temp_59, temp_235 * temp_65)));
    out_attr8.z = fma(0.0, temp_128, fma(temp_242, temp_80, fma(temp_238, temp_76, temp_235 * temp_79)));
    out_attr8.x = fma(0.0, temp_130, fma(temp_242, temp_73, fma(temp_238, temp_67, temp_235 * temp_72)));
    out_attr9.z = fma(0.0, temp_128, fma(temp_245, temp_80, fma(temp_240, temp_76, temp_236 * temp_79)));
    temp_254 = fma(temp_250, NnVfx2ViewParam.data[0].z, fma(temp_248, NnVfx2ViewParam.data[0].y, temp_247 * NnVfx2ViewParam.data[0].x)) + NnVfx2ViewParam.data[0].w;
    out_attr7.z = fma(0.0, temp_128, fma(temp_243, temp_80, fma(temp_239, temp_76, temp_234 * temp_79)));
    temp_255 = fma(temp_250, NnVfx2ViewParam.data[1].z, fma(temp_248, NnVfx2ViewParam.data[1].y, temp_247 * NnVfx2ViewParam.data[1].x)) + NnVfx2ViewParam.data[1].w;
    out_attr7.y = fma(0.0, temp_129, fma(temp_243, temp_64, fma(temp_239, temp_59, temp_234 * temp_65)));
    out_attr7.x = fma(0.0, temp_130, fma(temp_243, temp_73, fma(temp_239, temp_67, temp_234 * temp_72)));
    temp_256 = fma(temp_250, NnVfx2ViewParam.data[2].z, fma(temp_248, NnVfx2ViewParam.data[2].y, temp_247 * NnVfx2ViewParam.data[2].x)) + NnVfx2ViewParam.data[2].w;
    temp_257 = fma(temp_250, NnVfx2ViewParam.data[3].z, fma(temp_248, NnVfx2ViewParam.data[3].y, temp_247 * NnVfx2ViewParam.data[3].x)) + NnVfx2ViewParam.data[3].w;
    out_attr9.y = fma(0.0, temp_129, fma(temp_245, temp_64, fma(temp_240, temp_59, temp_236 * temp_65)));
    temp_258 = inversesqrt(fma(temp_256, temp_256, fma(temp_255, temp_255, temp_254 * temp_254)));
    out_attr2.y = fma(fma(temp_1, sysEmitterStaticUniformBlock.data[74].w, fma(temp_106, sysEmitterStaticUniformBlock.data[75].w, sysEmitterStaticUniformBlock.data[75].w + sysEmitterStaticUniformBlock.data[75].y)), fma(temp_249, temp_162, -0.5), (0.0 - fma(temp_249, (0.0 - float(temp_136 < 0 || !(temp_136 == 0) ? (0 - temp_246) + (temp_232 + (0 - (uint((0 - abs(temp_136) * temp_232)) >= uint(abs(temp_136)) ? -1 : 0)) ^ temp_246) : -1)), fma(temp_1, sysEmitterStaticUniformBlock.data[73].y, fma(temp_106 * sysEmitterStaticUniformBlock.data[74].y, -2.0, sysEmitterStaticUniformBlock.data[74].y + sysEmitterStaticUniformBlock.data[73].w))))) + 0.5;
    temp_259 = fma(temp_257, NnVfx2ViewParam.data[5].w, fma(temp_256, NnVfx2ViewParam.data[5].z, fma(temp_255, NnVfx2ViewParam.data[5].y, temp_254 * NnVfx2ViewParam.data[5].x)));
    gl_Position.y = temp_259;
    out_attr2.z = fma(fma(temp_1, sysEmitterStaticUniformBlock.data[79].z, fma(temp_195, sysEmitterStaticUniformBlock.data[80].z, sysEmitterStaticUniformBlock.data[80].x + sysEmitterStaticUniformBlock.data[80].z)), fma(temp_253, temp_144, -0.5), fma(temp_253, float(temp_152 < 0 || !(temp_152 == 0) ? (0 - temp_152 * (temp_218 + (0 - (uint((0 - temp_152 * temp_218)) >= uint(temp_152) ? -1 : 0)))) : -1), fma(temp_1, (0.0 - sysEmitterStaticUniformBlock.data[78].x), (0.0 - fma(temp_189 * sysEmitterStaticUniformBlock.data[79].x, -2.0, sysEmitterStaticUniformBlock.data[79].x + sysEmitterStaticUniformBlock.data[78].z))))) + 0.5;
    temp_260 = fma(temp_257, NnVfx2ViewParam.data[4].w, fma(temp_256, NnVfx2ViewParam.data[4].z, fma(temp_255, NnVfx2ViewParam.data[4].y, temp_254 * NnVfx2ViewParam.data[4].x)));
    gl_Position.x = temp_260;
    out_attr15.y = temp_255 * temp_258;
    temp_261 = 0.0 * temp_259;
    temp_262 = fma(temp_257, NnVfx2ViewParam.data[7].w, fma(temp_256, NnVfx2ViewParam.data[7].z, fma(temp_255, NnVfx2ViewParam.data[7].y, temp_254 * NnVfx2ViewParam.data[7].x)));
    temp_263 = (0 - int(uint(temp_152) >> 31));
    gl_Position.w = temp_262;
    temp_264 = fma(temp_257, NnVfx2ViewParam.data[6].w, fma(temp_256, NnVfx2ViewParam.data[6].z, fma(temp_255, NnVfx2ViewParam.data[6].y, temp_254 * NnVfx2ViewParam.data[6].x)));
    gl_Position.z = temp_264;
    out_attr15.x = temp_254 * temp_258;
    out_attr15.z = temp_256 * temp_258;
    temp_265 = fma(0.0, temp_260, temp_261);
    out_attr3.y = fma(temp_262, 0.5, fma(0.0, temp_264, fma(0.0, temp_260, temp_259 * -0.5)));
    temp_266 = temp_262 + fma(0.0, temp_264, temp_265);
    out_attr3.w = temp_266;
    temp_267 = clamp(fma(1.0 / fma(fma(temp_213, 0.5, temp_210 * 0.5) * (1.0 / fma(0.0, temp_213, temp_210)), NnVfx2ViewParam.data[30].w, (0.0 - NnVfx2ViewParam.data[30].y)), (0.0 - NnVfx2ViewParam.data[30].z), (0.0 - sysEmitterStaticUniformBlock.data[137].x)) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[137].x) + sysEmitterStaticUniformBlock.data[137].y)), 0.0, 1.0);
    out_attr11.x = sysCustomShaderUniformBlock0.data[36].w;
    out_attr1.z = fma(temp_147, sysEmitterStaticUniformBlock.data[121].z, fma(fma(temp_133, (sysEmitterStaticUniformBlock.data[121].z + (0.0 - sysEmitterStaticUniformBlock.data[120].z)) * temp_122, sysEmitterStaticUniformBlock.data[120].z), temp_158, fma(temp_142, (0.0 - sysEmitterStaticUniformBlock.data[120].z), sysEmitterStaticUniformBlock.data[120].z))) * NnVfx2EmitterDynamicParam.data[1].z * sysEmitterStaticUniformBlock.data[103].x;
    out_attr4.x = temp_267 * NnVfx2EmitterDynamicParam.data[3].x;
    out_attr9.x = fma(0.0, temp_130, fma(temp_245, temp_73, fma(temp_240, temp_67, temp_236 * temp_72)));
    out_attr2.x = fma(fma(temp_251, temp_143, -0.5), fma(temp_1, sysEmitterStaticUniformBlock.data[74].z, fma(temp_57, sysEmitterStaticUniformBlock.data[75].z, sysEmitterStaticUniformBlock.data[75].x + sysEmitterStaticUniformBlock.data[75].z)), fma(temp_251, float(temp_136 < 0 || !(temp_136 == 0) ? (0 - temp_136 * (temp_217 + (0 - (uint((0 - temp_136 * temp_217)) >= uint(temp_136) ? -1 : 0)))) : -1), fma(temp_1, (0.0 - sysEmitterStaticUniformBlock.data[73].x), (0.0 - fma(temp_57 * sysEmitterStaticUniformBlock.data[74].x, -2.0, sysEmitterStaticUniformBlock.data[74].x + sysEmitterStaticUniformBlock.data[73].z))))) + 0.5;
    out_attr10.x = (0.0 - fma(temp_250, sysCustomShaderUniformBlock0.data[38].z, fma(temp_248, sysCustomShaderUniformBlock0.data[38].y, temp_247 * sysCustomShaderUniformBlock0.data[38].x))) + -0.0;
    out_attr2.w = fma(fma(temp_1, sysEmitterStaticUniformBlock.data[79].w, fma(temp_196, sysEmitterStaticUniformBlock.data[80].w, sysEmitterStaticUniformBlock.data[80].w + sysEmitterStaticUniformBlock.data[80].y)), fma(temp_252, temp_164, -0.5), (0.0 - fma(temp_252, (0.0 - float(temp_152 < 0 || !(temp_152 == 0) ? (0 - temp_263) + (temp_227 + (0 - (uint((0 - abs(temp_152) * temp_227)) >= uint(abs(temp_152)) ? -1 : 0)) ^ temp_263) : -1)), fma(temp_1, sysEmitterStaticUniformBlock.data[78].y, fma(temp_192 * sysEmitterStaticUniformBlock.data[79].y, -2.0, sysEmitterStaticUniformBlock.data[79].y + sysEmitterStaticUniformBlock.data[78].w))))) + 0.5;
    out_attr3.x = fma(temp_262, 0.5, fma(0.0, temp_264, fma(temp_260, 0.5, temp_261)));
    if (0.0 < sysCustomShaderUniformBlock1.data[4].w)
    {
        temp_268 = (0.0 - temp_130) + temp_247;
        temp_269 = (0.0 - temp_129) + temp_248;
        temp_270 = (0.0 - temp_128) + temp_250;
        out_attr13.x = fma(fma(temp_270, NnVfx2ViewParam.data[0].z, fma(temp_269, NnVfx2ViewParam.data[0].y, temp_268 * NnVfx2ViewParam.data[0].x)), sysCustomShaderUniformBlock0.data[31].x, 0.5) * sysCustomShaderUniformBlock0.data[41].x;
        out_attr13.y = fma(fma(temp_270, NnVfx2ViewParam.data[1].z, fma(temp_269, NnVfx2ViewParam.data[1].y, temp_268 * NnVfx2ViewParam.data[1].x)), (0.0 - sysCustomShaderUniformBlock0.data[31].y), 0.5) * sysCustomShaderUniformBlock0.data[41].x;
    }
    out_attr14.x = fma(1.0 / fma(fma(temp_262, 0.5, fma(temp_264, 0.5, temp_265)) * (1.0 / temp_266), NnVfx2ViewParam.data[30].w, (0.0 - NnVfx2ViewParam.data[30].y)), NnVfx2ViewParam.data[30].z, -0.0);
    if (!(temp_267 <= 0.0))
    {
        return;
    }
    gl_Position.x = 0.0;
    gl_Position.y = 0.0;
    gl_Position.z = NnVfx2ViewParam.data[30].y * 5.0;
    out_attr4.x = 0.0;
    return;
}
