// static_grsn.bfsha model VfxGeneralShader program 1940 (vert)
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
    precise float temp_116;
    precise float temp_117;
    precise float temp_118;
    precise float temp_119;
    bool temp_120;
    precise float temp_121;
    bool temp_122;
    precise float temp_123;
    precise float temp_124;
    precise float temp_125;
    int temp_126;
    int temp_127;
    precise float temp_128;
    int temp_129;
    bool temp_130;
    precise float temp_131;
    precise float temp_132;
    precise float temp_133;
    precise float temp_134;
    precise float temp_135;
    precise float temp_136;
    precise float temp_137;
    precise float temp_138;
    int temp_139;
    precise float temp_140;
    precise float temp_141;
    precise float temp_142;
    int temp_143;
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
    bool temp_158;
    precise float temp_159;
    int temp_160;
    precise float temp_161;
    precise float temp_162;
    precise float temp_163;
    int temp_164;
    uint temp_165;
    int temp_166;
    precise float temp_167;
    precise float temp_168;
    int temp_169;
    precise float temp_170;
    precise float temp_171;
    precise float temp_172;
    bool temp_173;
    uint temp_174;
    precise float temp_175;
    bool temp_176;
    precise float temp_177;
    precise float temp_178;
    precise float temp_179;
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
    precise float temp_198;
    int temp_199;
    precise float temp_200;
    precise float temp_201;
    precise float temp_202;
    int temp_203;
    precise float temp_204;
    uint temp_205;
    precise float temp_206;
    uint temp_207;
    precise float temp_208;
    precise float temp_209;
    precise float temp_210;
    precise float temp_211;
    precise float temp_212;
    int temp_213;
    precise float temp_214;
    precise float temp_215;
    precise float temp_216;
    precise float temp_217;
    precise float temp_218;
    precise float temp_219;
    precise float temp_220;
    precise float temp_221;
    precise float temp_222;
    int temp_223;
    precise float temp_224;
    precise float temp_225;
    precise float temp_226;
    precise float temp_227;
    precise float temp_228;
    int temp_229;
    int temp_230;
    precise float temp_231;
    precise float temp_232;
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
    int temp_243;
    int temp_244;
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
    temp_24 = sysScaleAttr.w;
    temp_25 = sqrt(temp_20);
    temp_26 = temp_19;
    temp_27 = temp_20;
    temp_28 = temp_8;
    if (temp_10)
    {
        temp_25 = temp_8 * temp_8;
    }
    temp_29 = temp_25;
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
    temp_34 = intBitsToFloat(undef);
    if (temp_22)
    {
        temp_34 = inversesqrt(temp_19);
    }
    temp_35 = temp_34;
    temp_36 = intBitsToFloat(undef);
    temp_37 = temp_35;
    if (temp_10)
    {
        temp_36 = temp_33 * 0.5 * sysEmitterStaticUniformBlock.data[13].y;
    }
    temp_38 = intBitsToFloat(undef);
    temp_39 = temp_36;
    if (temp_23)
    {
        temp_38 = inversesqrt(temp_20);
    }
    temp_40 = temp_38;
    temp_41 = intBitsToFloat(undef);
    if (temp_10)
    {
        temp_41 = temp_33 * 0.5 * sysEmitterStaticUniformBlock.data[13].z;
    }
    temp_42 = intBitsToFloat(undef);
    temp_43 = temp_41;
    if (temp_10)
    {
        temp_42 = temp_33 * 0.5 * sysEmitterStaticUniformBlock.data[13].x;
    }
    temp_44 = temp_42;
    temp_45 = intBitsToFloat(undef);
    if (!temp_10)
    {
        temp_46 = temp_8 * log2(abs(sysEmitterStaticUniformBlock.data[14].x));
        temp_47 = 1.0 / log2(sysEmitterStaticUniformBlock.data[14].x);
        temp_48 = temp_47 * 1.44269502;
        temp_49 = (temp_8 + (0.0 - fma(temp_48, exp2(temp_46), (0.0 - temp_48)))) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[14].x) + 1.0)) * sysEmitterStaticUniformBlock.data[13].w;
        temp_39 = temp_49 * sysEmitterStaticUniformBlock.data[13].y;
        temp_44 = temp_49 * sysEmitterStaticUniformBlock.data[13].x;
        temp_26 = temp_47;
        temp_43 = temp_49 * sysEmitterStaticUniformBlock.data[13].z;
        temp_45 = temp_46;
        temp_27 = temp_49;
    }
    temp_50 = temp_39;
    temp_51 = temp_44;
    temp_52 = temp_43;
    temp_53 = intBitsToFloat(undef);
    temp_54 = temp_26;
    temp_55 = temp_45;
    temp_56 = temp_27;
    if (temp_21)
    {
        temp_53 = temp_32 * temp_9;
    }
    temp_57 = sysRandomAttr.x;
    temp_58 = temp_53;
    if (!temp_21)
    {
        temp_58 = 0.0;
    }
    temp_59 = temp_58;
    temp_60 = intBitsToFloat(undef);
    if (temp_22)
    {
        temp_60 = temp_35 * temp_13;
    }
    temp_61 = intBitsToFloat(undef);
    temp_62 = temp_60;
    if (temp_23)
    {
        temp_61 = temp_40 * temp_16;
    }
    temp_63 = temp_61;
    if (!temp_22)
    {
        temp_62 = 0.0;
    }
    temp_64 = temp_62;
    if (!temp_23)
    {
        temp_63 = 0.0;
    }
    temp_65 = temp_63;
    if (temp_21)
    {
        temp_54 = temp_32 * temp_7;
    }
    temp_66 = temp_54;
    if (!temp_21)
    {
        temp_66 = 0.0;
    }
    temp_67 = temp_66;
    temp_68 = intBitsToFloat(undef);
    if (temp_22)
    {
        temp_68 = temp_35 * temp_12;
    }
    temp_69 = intBitsToFloat(undef);
    temp_70 = temp_68;
    if (temp_23)
    {
        temp_69 = temp_40 * temp_15;
    }
    temp_71 = temp_69;
    if (!temp_22)
    {
        temp_70 = 0.0;
    }
    temp_72 = temp_70;
    if (!temp_23)
    {
        temp_71 = 0.0;
    }
    temp_73 = temp_71;
    if (temp_22)
    {
        temp_55 = temp_35 * temp_14;
    }
    temp_74 = temp_55;
    if (temp_21)
    {
        temp_37 = temp_32 * temp_11;
    }
    temp_75 = temp_37;
    if (!temp_21)
    {
        temp_75 = 0.0;
    }
    temp_76 = temp_75;
    if (temp_23)
    {
        temp_56 = temp_40 * temp_17;
    }
    temp_77 = temp_56;
    if (!temp_22)
    {
        temp_74 = 0.0;
    }
    temp_78 = temp_74;
    if (!temp_23)
    {
        temp_77 = 0.0;
    }
    temp_79 = temp_77;
    if (!temp_10)
    {
        temp_80 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[14].x) + 1.0);
        temp_28 = fma(exp2(temp_8 * log2(abs(sysEmitterStaticUniformBlock.data[14].x))), (0.0 - temp_80), temp_80);
    }
    temp_81 = temp_28;
    temp_82 = fma(fma(temp_81, sysLocalVecAttr.x, fma(temp_52, temp_76, fma(temp_51, temp_67, temp_50 * temp_59))), temp_24, sysLocalPosAttr.x);
    temp_83 = fma(fma(temp_81, sysLocalVecAttr.y, fma(temp_52, temp_78, fma(temp_51, temp_72, temp_50 * temp_64))), temp_24, sysLocalPosAttr.y);
    temp_84 = fma(fma(temp_81, sysLocalVecAttr.z, fma(temp_52, temp_79, fma(temp_51, temp_73, temp_50 * temp_65))), temp_24, sysLocalPosAttr.z);
    if (0.0 < sysEmitterStaticUniformBlock.data[11].x)
    {
        temp_85 = fma(temp_57 * sysEmitterStaticUniformBlock.data[12].y, sysEmitterStaticUniformBlock.data[11].x, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[11].x);
        temp_86 = temp_85 + (0.0 - floor(temp_85));
    }
    else
    {
        temp_86 = temp_1 * (1.0 / temp_2);
    }
    temp_87 = temp_86;
    temp_88 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[140].w) + sysEmitterStaticUniformBlock.data[141].w);
    temp_89 = 1.0 / (sysEmitterStaticUniformBlock.data[142].w + (0.0 - sysEmitterStaticUniformBlock.data[141].w));
    temp_90 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[142].w) + sysEmitterStaticUniformBlock.data[143].w);
    temp_91 = 1.0 / (sysEmitterStaticUniformBlock.data[144].w + (0.0 - sysEmitterStaticUniformBlock.data[143].w));
    temp_92 = temp_87 >= sysEmitterStaticUniformBlock.data[140].w ? 1.0 : 0.0;
    temp_93 = temp_87 + (0.0 - sysEmitterStaticUniformBlock.data[140].w);
    temp_94 = temp_87 >= sysEmitterStaticUniformBlock.data[141].w ? 1.0 : 0.0;
    temp_95 = temp_87 + (0.0 - sysEmitterStaticUniformBlock.data[141].w);
    temp_96 = temp_87 >= sysEmitterStaticUniformBlock.data[142].w ? 1.0 : 0.0;
    temp_97 = fma(temp_92, (0.0 - temp_94), temp_92);
    temp_98 = temp_87 + (0.0 - sysEmitterStaticUniformBlock.data[142].w);
    temp_99 = fma(temp_94, (0.0 - temp_96), temp_94);
    temp_100 = temp_87 >= sysEmitterStaticUniformBlock.data[143].w ? 1.0 : 0.0;
    temp_101 = temp_87 + (0.0 - sysEmitterStaticUniformBlock.data[143].w);
    temp_102 = temp_87 >= sysEmitterStaticUniformBlock.data[144].w ? 1.0 : 0.0;
    temp_103 = fma(temp_96, (0.0 - temp_100), temp_96);
    temp_104 = fma(temp_100, (0.0 - temp_102), temp_100);
    if (0.0 < sysEmitterStaticUniformBlock.data[10].y)
    {
        temp_105 = fma(temp_57 * sysEmitterStaticUniformBlock.data[11].z, sysEmitterStaticUniformBlock.data[10].y, temp_1) * (1.0 / sysEmitterStaticUniformBlock.data[10].y);
        temp_106 = temp_105 + (0.0 - floor(temp_105));
    }
    else
    {
        temp_106 = temp_1 * (1.0 / temp_2);
    }
    temp_107 = temp_106;
    temp_108 = sysRandomAttr.y;
    temp_109 = sysPosAttr.z;
    temp_110 = sysPosAttr.y;
    temp_111 = sysPosAttr.x;
    temp_112 = sysRandomAttr.z;
    temp_113 = sysEmtMat1Attr.w;
    temp_114 = sysInitRotateAttr.x;
    temp_115 = sysNormalAttr.x;
    temp_116 = sysNormalAttr.y;
    temp_117 = sysNormalAttr.z;
    temp_118 = sysInitRotateAttr.y;
    temp_119 = sysInitRotateAttr.z;
    temp_120 = ((!((1 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 1) || !(temp_57 > 0.5) ? -1 : 0)) != 0;
    temp_121 = fma(temp_102, sysEmitterStaticUniformBlock.data[144].z, fma(fma((sysEmitterStaticUniformBlock.data[144].z + (0.0 - sysEmitterStaticUniformBlock.data[143].z)) * temp_91, temp_101, sysEmitterStaticUniformBlock.data[143].z), temp_104, fma(fma(((0.0 - sysEmitterStaticUniformBlock.data[142].z) + sysEmitterStaticUniformBlock.data[143].z) * temp_90, temp_98, sysEmitterStaticUniformBlock.data[142].z), temp_103, fma(fma((sysEmitterStaticUniformBlock.data[142].z + (0.0 - sysEmitterStaticUniformBlock.data[141].z)) * temp_89, temp_95, sysEmitterStaticUniformBlock.data[141].z), temp_99, fma(fma(temp_93, (sysEmitterStaticUniformBlock.data[141].z + (0.0 - sysEmitterStaticUniformBlock.data[140].z)) * temp_88, sysEmitterStaticUniformBlock.data[140].z), temp_97, fma(temp_92, (0.0 - sysEmitterStaticUniformBlock.data[140].z), sysEmitterStaticUniformBlock.data[140].z)))))) * sysScaleAttr.z * NnVfx2EmitterDynamicParam.data[3].w * fma(0.5, sysEmitterStaticUniformBlock.data[15].z, temp_109);
    temp_122 = sysRandomAttr.w > 0.5;
    temp_123 = floor(temp_57 * 2.0);
    temp_124 = sysTexCoordAttr.x;
    temp_125 = fma(temp_102, sysEmitterStaticUniformBlock.data[144].y, fma(fma((sysEmitterStaticUniformBlock.data[144].y + (0.0 - sysEmitterStaticUniformBlock.data[143].y)) * temp_91, temp_101, sysEmitterStaticUniformBlock.data[143].y), temp_104, fma(fma(((0.0 - sysEmitterStaticUniformBlock.data[142].y) + sysEmitterStaticUniformBlock.data[143].y) * temp_90, temp_98, sysEmitterStaticUniformBlock.data[142].y), temp_103, fma(fma((sysEmitterStaticUniformBlock.data[142].y + (0.0 - sysEmitterStaticUniformBlock.data[141].y)) * temp_89, temp_95, sysEmitterStaticUniformBlock.data[141].y), temp_99, fma(fma(temp_93, (sysEmitterStaticUniformBlock.data[141].y + (0.0 - sysEmitterStaticUniformBlock.data[140].y)) * temp_88, sysEmitterStaticUniformBlock.data[140].y), temp_97, fma(temp_92, (0.0 - sysEmitterStaticUniformBlock.data[140].y), sysEmitterStaticUniformBlock.data[140].y)))))) * sysScaleAttr.y * NnVfx2EmitterDynamicParam.data[3].z * fma(0.5, sysEmitterStaticUniformBlock.data[15].y, temp_110);
    temp_126 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x10000000;
    temp_127 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x20000000;
    temp_128 = (clamp(min(0.0, temp_57) + -0.0, 0.0, 1.0) + sysScaleAttr.x) * fma(temp_102, sysEmitterStaticUniformBlock.data[144].x, fma(fma((sysEmitterStaticUniformBlock.data[144].x + (0.0 - sysEmitterStaticUniformBlock.data[143].x)) * temp_91, temp_101, sysEmitterStaticUniformBlock.data[143].x), temp_104, fma(fma(((0.0 - sysEmitterStaticUniformBlock.data[142].x) + sysEmitterStaticUniformBlock.data[143].x) * temp_90, temp_98, sysEmitterStaticUniformBlock.data[142].x), temp_103, fma(fma((sysEmitterStaticUniformBlock.data[142].x + (0.0 - sysEmitterStaticUniformBlock.data[141].x)) * temp_89, temp_95, sysEmitterStaticUniformBlock.data[141].x), temp_99, fma(fma(temp_93, (sysEmitterStaticUniformBlock.data[141].x + (0.0 - sysEmitterStaticUniformBlock.data[140].x)) * temp_88, sysEmitterStaticUniformBlock.data[140].x), temp_97, fma(temp_92, (0.0 - sysEmitterStaticUniformBlock.data[140].x), sysEmitterStaticUniformBlock.data[140].x)))))) * NnVfx2EmitterDynamicParam.data[3].y * fma(0.5, sysEmitterStaticUniformBlock.data[15].x, temp_111);
    temp_129 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x40000000;
    temp_130 = 0.0 == sysEmitterStaticUniformBlock.data[162].w;
    temp_131 = fma(temp_84, temp_15, fma(temp_83, temp_12, temp_82 * temp_7)) + sysEmtMat0Attr.w;
    temp_132 = fma(temp_84, temp_17, fma(temp_83, temp_14, temp_82 * temp_11)) + sysEmtMat2Attr.w;
    temp_133 = floor(temp_112 * 2.0);
    temp_134 = fma(temp_84, temp_16, fma(temp_83, temp_13, temp_82 * temp_9)) + temp_113;
    temp_135 = temp_113;
    temp_136 = intBitsToFloat((temp_122 ? -1 : 0));
    temp_137 = temp_124;
    if (!temp_130)
    {
        temp_135 = log2(abs(sysEmitterStaticUniformBlock.data[162].w));
    }
    temp_138 = temp_135;
    temp_139 = int(trunc(sysEmitterStaticUniformBlock.data[77].z));
    temp_140 = sysTexCoordAttr.y;
    temp_141 = floor(temp_108 * 2.0);
    temp_142 = fma(fma(temp_57 + temp_108, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].x, 2.0, sysEmitterStaticUniformBlock.data[162].x);
    temp_143 = int(trunc(sysEmitterStaticUniformBlock.data[82].z));
    temp_144 = temp_138;
    temp_145 = 2.0;
    temp_146 = temp_140;
    if (!temp_130)
    {
        temp_144 = temp_1 * temp_138;
    }
    temp_147 = temp_144;
    temp_148 = temp_147;
    if (!temp_130)
    {
        temp_136 = temp_147;
    }
    temp_149 = ((0.0 - temp_123 < 0.0 ? 1.0 : 0.0) + (temp_123 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_127 > 0 ? -1 : 0)) + (0 - temp_127 >= 0 ? 0 : 1)));
    temp_150 = fma(fma(temp_57 + temp_112, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].z, 2.0, sysEmitterStaticUniformBlock.data[162].z);
    temp_151 = fma(fma(temp_108 + temp_112, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].y, 2.0, sysEmitterStaticUniformBlock.data[162].y);
    if (!temp_130)
    {
        temp_145 = exp2(temp_136);
    }
    temp_152 = temp_107 >= sysEmitterStaticUniformBlock.data[112].w ? 1.0 : 0.0;
    temp_153 = temp_107 >= sysEmitterStaticUniformBlock.data[113].w ? 1.0 : 0.0;
    temp_154 = temp_124;
    temp_155 = temp_145;
    if (!temp_120)
    {
        temp_154 = (0.0 - temp_124) + 1.0;
    }
    temp_156 = fma(temp_152, (0.0 - sysEmitterStaticUniformBlock.data[112].x), sysEmitterStaticUniformBlock.data[112].x);
    temp_157 = temp_156;
    temp_158 = sysEmitterStaticUniformBlock.data[162].w == 1.0;
    temp_159 = ((0.0 - temp_141 < 0.0 ? 1.0 : 0.0) + (temp_141 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_129 > 0 ? -1 : 0)) + (0 - temp_129 >= 0 ? 0 : 1)));
    temp_160 = floatBitsToInt(1.0 / float(uint(temp_139))) + -2;
    temp_161 = fma(fma((sysEmitterStaticUniformBlock.data[113].x + (0.0 - sysEmitterStaticUniformBlock.data[112].x)) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[112].w) + sysEmitterStaticUniformBlock.data[113].w)), temp_107 + (0.0 - sysEmitterStaticUniformBlock.data[112].w), sysEmitterStaticUniformBlock.data[112].x), fma(temp_153, (0.0 - temp_152), temp_152), temp_156);
    temp_162 = temp_107 >= sysEmitterStaticUniformBlock.data[114].w ? 1.0 : 0.0;
    temp_163 = ((0.0 - temp_133 < 0.0 ? 1.0 : 0.0) + (temp_133 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_126 > 0 ? -1 : 0)) + (0 - temp_126 >= 0 ? 0 : 1)));
    temp_164 = floatBitsToInt(1.0 / float(uint(temp_143))) + -2;
    temp_165 = uint(max(trunc(float(0u) * intBitsToFloat(temp_160)), 0.0));
    temp_166 = 0;
    temp_167 = temp_140;
    temp_168 = temp_161;
    if ((1 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].z)) != 1)
    {
        temp_166 = 1;
    }
    temp_169 = temp_166;
    if (!temp_158)
    {
        temp_148 = (0.0 - sysEmitterStaticUniformBlock.data[162].w) + 1.0;
    }
    temp_170 = temp_148;
    temp_171 = temp_170;
    if (!(((!((4 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 4) || !(temp_112 > 0.5) ? -1 : 0)) != 0))
    {
        temp_137 = (0.0 - temp_124) + 1.0;
    }
    if (!temp_158)
    {
        temp_171 = 1.0 / temp_170;
    }
    temp_172 = temp_171;
    temp_173 = temp_169 == 1;
    temp_174 = uint(max(trunc(float(0u) * intBitsToFloat(temp_164)), 0.0));
    temp_175 = temp_172;
    if (temp_130)
    {
        temp_155 = 1.0;
    }
    temp_176 = temp_109 == 0.0 && temp_111 == 0.0 && temp_110 == 0.0;
    if (!(((!((2 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 2) || !(temp_108 > 0.5) ? -1 : 0)) != 0))
    {
        temp_167 = (0.0 - temp_140) + 1.0;
    }
    temp_177 = intBitsToFloat(undef);
    if (!temp_158)
    {
        temp_177 = fma(temp_172, (0.0 - temp_155), temp_172);
    }
    temp_178 = temp_177;
    temp_179 = temp_57;
    temp_180 = temp_108;
    temp_181 = temp_57;
    temp_182 = temp_108;
    if (temp_158)
    {
        temp_178 = temp_1;
    }
    temp_183 = temp_178;
    if (!(((!((8 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 8) || !temp_122 ? -1 : 0)) != 0))
    {
        temp_146 = (0.0 - temp_140) + 1.0;
    }
    if (temp_176)
    {
        temp_175 = temp_115;
    }
    temp_184 = temp_175;
    if (temp_176)
    {
        temp_168 = temp_116;
    }
    temp_185 = temp_168;
    if (temp_176)
    {
        temp_157 = temp_117;
    }
    temp_186 = temp_157;
    if (temp_173)
    {
        temp_179 = temp_108;
    }
    temp_187 = temp_179;
    temp_188 = temp_187;
    temp_189 = temp_187;
    if (temp_173)
    {
        temp_180 = temp_112;
    }
    temp_190 = temp_180;
    temp_191 = temp_190;
    temp_192 = temp_190;
    if (temp_173)
    {
        temp_181 = temp_108;
    }
    temp_193 = temp_181;
    temp_194 = temp_193;
    temp_195 = temp_193;
    if (temp_173)
    {
        temp_182 = temp_112;
    }
    temp_196 = temp_182;
    if (!temp_173)
    {
        temp_197 = temp_169 == 2;
        if (temp_197)
        {
            temp_188 = temp_112;
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
            temp_196 = temp_108;
        }
    }
    out_attr12.x = temp_131;
    out_attr12.y = temp_134;
    out_attr12.z = temp_132;
    temp_198 = sysTangentAttr.y;
    temp_199 = floatBitsToInt(1.0 / float(uint(abs(temp_139)))) + -2;
    temp_200 = sysTangentAttr.z;
    if (!temp_176)
    {
        temp_186 = fma(temp_109, sysEmitterStaticUniformBlock.data[14].y, temp_117);
    }
    temp_201 = temp_186;
    temp_202 = sysTangentAttr.x;
    temp_203 = floatBitsToInt(1.0 / float(uint(abs(temp_143)))) + -2;
    if (!temp_176)
    {
        temp_185 = fma(temp_110, sysEmitterStaticUniformBlock.data[14].y, temp_116);
    }
    temp_204 = temp_185;
    temp_205 = uint(max(trunc(intBitsToFloat(temp_199) * float(0u)), 0.0));
    if (!temp_176)
    {
        temp_184 = fma(temp_111, sysEmitterStaticUniformBlock.data[14].y, temp_115);
    }
    temp_206 = temp_184;
    temp_207 = uint(max(trunc(float(0u) * intBitsToFloat(temp_203)), 0.0));
    temp_208 = sysTangentAttr.w;
    temp_209 = fma(fma(temp_142 * temp_163, -2.0, temp_142), temp_183, fma(temp_57 + -0.5, sysEmitterStaticUniformBlock.data[161].x, fma(temp_163 * temp_114, -2.0, temp_114)));
    temp_210 = fma(fma(temp_151 * temp_149, -2.0, temp_151), temp_183, fma(temp_108 + -0.5, sysEmitterStaticUniformBlock.data[161].y, fma(temp_149 * temp_118, -2.0, temp_118)));
    temp_211 = fma(fma(temp_150 * temp_159, -2.0, temp_150), temp_183, fma(temp_112 + -0.5, sysEmitterStaticUniformBlock.data[161].z, fma(temp_159 * temp_119, -2.0, temp_119)));
    temp_212 = fma(temp_117, temp_202, (0.0 - temp_115 * temp_200)) * temp_208;
    temp_213 = int(temp_165) + int(uint(max(trunc(intBitsToFloat(temp_160) * float(uint((0 - temp_139 * int(temp_165))))), 0.0)));
    temp_214 = cos(temp_210) * cos(temp_209);
    temp_215 = sin(temp_209) * cos(temp_210);
    temp_216 = cos(temp_210) * cos(temp_211);
    temp_217 = sin(temp_209) * sin(temp_210);
    temp_218 = sin(temp_210) * cos(temp_209);
    temp_219 = cos(temp_209) * cos(temp_211);
    temp_220 = sin(temp_209) * cos(temp_211);
    temp_221 = fma(temp_116, temp_200, (0.0 - temp_117 * temp_198)) * temp_208;
    temp_222 = sin(temp_210) * cos(temp_211);
    temp_223 = int(temp_205) + int(uint(max(trunc(intBitsToFloat(temp_199) * float(uint((0 - abs(temp_139) * int(temp_205))))), 0.0)));
    temp_224 = fma(temp_115, temp_198, (0.0 - temp_116 * temp_202)) * temp_208;
    temp_225 = fma(sin(temp_211), temp_214, temp_217);
    temp_226 = fma(sin(temp_211), temp_215, (0.0 - temp_218));
    temp_227 = fma(sin(temp_211), temp_218, (0.0 - temp_215));
    temp_228 = fma(sin(temp_211), temp_217, temp_214);
    temp_229 = int(temp_174) + int(uint(max(trunc(intBitsToFloat(temp_164) * float(uint((0 - temp_143 * int(temp_174))))), 0.0)));
    temp_230 = int(temp_207) + int(uint(max(trunc(intBitsToFloat(temp_203) * float(uint((0 - abs(temp_143) * int(temp_207))))), 0.0)));
    temp_231 = 0.0 + fma(temp_121, temp_222, fma(temp_128, temp_216, sin(temp_211) * (0.0 - temp_125)));
    temp_232 = 0.0 + fma(temp_222, temp_201, fma(temp_216, temp_206, sin(temp_211) * (0.0 - temp_204)));
    temp_233 = 0.0 + fma(temp_222, temp_200, fma(temp_216, temp_202, sin(temp_211) * (0.0 - temp_198)));
    temp_234 = 0.0 + fma(temp_222, temp_224, fma(temp_216, temp_221, sin(temp_211) * (0.0 - temp_212)));
    temp_235 = 0.0 + fma(temp_227, temp_121, fma(temp_225, temp_128, temp_125 * temp_219));
    temp_236 = 0.0 + fma(temp_227, temp_201, fma(temp_225, temp_206, temp_219 * temp_204));
    temp_237 = 0.0 + fma(temp_227, temp_224, fma(temp_225, temp_221, temp_219 * temp_212));
    temp_238 = 0.0 + fma(temp_227, temp_200, fma(temp_225, temp_202, temp_219 * temp_198));
    temp_239 = 0.0 + fma(temp_228, temp_224, fma(temp_226, temp_221, temp_220 * temp_212));
    temp_240 = 0.0 + fma(temp_228, temp_121, fma(temp_226, temp_128, temp_125 * temp_220));
    temp_241 = 0.0 + fma(temp_228, temp_200, fma(temp_226, temp_202, temp_220 * temp_198));
    temp_242 = 0.0 + fma(temp_228, temp_201, fma(temp_226, temp_206, temp_220 * temp_204));
    out_attr5.w = sysVertexColor0Attr.w;
    out_attr5.y = sysVertexColor0Attr.y;
    out_attr5.x = sysVertexColor0Attr.x;
    temp_243 = (0 - int(uint(temp_139) >> 31));
    out_attr5.z = sysVertexColor0Attr.z;
    temp_244 = (0 - int(uint(temp_143) >> 31));
    temp_245 = fma(0.0, temp_121, fma(0.0, temp_128, 0.0 * temp_125)) + 1.0;
    temp_246 = fma(temp_132, temp_245, fma(temp_240, temp_79, fma(temp_235, temp_78, temp_231 * temp_76)));
    temp_247 = fma(temp_131, temp_245, fma(temp_240, temp_73, fma(temp_235, temp_72, temp_231 * temp_67)));
    out_attr6.z = temp_246;
    temp_248 = fma(temp_134, temp_245, fma(temp_240, temp_65, fma(temp_235, temp_64, temp_231 * temp_59)));
    out_attr6.x = temp_247;
    out_attr6.y = temp_248;
    out_attr4.x = NnVfx2EmitterDynamicParam.data[3].x;
    out_attr0.x = sysEmitterStaticUniformBlock.data[104].x * NnVfx2EmitterDynamicParam.data[0].x * sysEmitterStaticUniformBlock.data[103].x;
    temp_249 = 1.0 / sysEmitterStaticUniformBlock.data[77].w * sysEmitterStaticUniformBlock.data[77].y;
    out_attr0.y = sysEmitterStaticUniformBlock.data[104].y * NnVfx2EmitterDynamicParam.data[0].y * sysEmitterStaticUniformBlock.data[103].x;
    out_attr0.z = sysEmitterStaticUniformBlock.data[104].z * NnVfx2EmitterDynamicParam.data[0].z * sysEmitterStaticUniformBlock.data[103].x;
    temp_250 = 1.0 / sysEmitterStaticUniformBlock.data[77].z * sysEmitterStaticUniformBlock.data[77].x;
    out_attr9.z = fma(0.0, temp_132, fma(temp_239, temp_79, fma(temp_237, temp_78, temp_234 * temp_76)));
    temp_251 = 1.0 / sysEmitterStaticUniformBlock.data[82].w * sysEmitterStaticUniformBlock.data[82].y;
    temp_252 = 1.0 / sysEmitterStaticUniformBlock.data[82].z * sysEmitterStaticUniformBlock.data[82].x;
    out_attr8.z = fma(0.0, temp_132, fma(temp_241, temp_79, fma(temp_238, temp_78, temp_233 * temp_76)));
    out_attr8.y = fma(0.0, temp_134, fma(temp_241, temp_65, fma(temp_238, temp_64, temp_233 * temp_59)));
    out_attr7.z = fma(0.0, temp_132, fma(temp_242, temp_79, fma(temp_236, temp_78, temp_232 * temp_76)));
    out_attr8.x = fma(0.0, temp_131, fma(temp_241, temp_73, fma(temp_238, temp_72, temp_233 * temp_67)));
    out_attr9.x = fma(0.0, temp_131, fma(temp_239, temp_73, fma(temp_237, temp_72, temp_234 * temp_67)));
    out_attr7.y = fma(0.0, temp_134, fma(temp_242, temp_65, fma(temp_236, temp_64, temp_232 * temp_59)));
    temp_253 = fma(temp_246, NnVfx2ViewParam.data[0].z, fma(temp_248, NnVfx2ViewParam.data[0].y, temp_247 * NnVfx2ViewParam.data[0].x)) + NnVfx2ViewParam.data[0].w;
    out_attr7.x = fma(0.0, temp_131, fma(temp_242, temp_73, fma(temp_236, temp_72, temp_232 * temp_67)));
    temp_254 = fma(temp_246, NnVfx2ViewParam.data[1].z, fma(temp_248, NnVfx2ViewParam.data[1].y, temp_247 * NnVfx2ViewParam.data[1].x)) + NnVfx2ViewParam.data[1].w;
    out_attr2.w = fma(fma(temp_1, sysEmitterStaticUniformBlock.data[79].w, fma(temp_196, sysEmitterStaticUniformBlock.data[80].w, sysEmitterStaticUniformBlock.data[80].w + sysEmitterStaticUniformBlock.data[80].y)), fma(temp_251, temp_146, -0.5), (0.0 - fma(temp_251, (0.0 - float(temp_143 < 0 || !(temp_143 == 0) ? (0 - temp_244) + (temp_230 + (0 - (uint((0 - abs(temp_143) * temp_230)) >= uint(abs(temp_143)) ? -1 : 0)) ^ temp_244) : -1)), fma(temp_1, sysEmitterStaticUniformBlock.data[78].y, fma(temp_192 * sysEmitterStaticUniformBlock.data[79].y, -2.0, sysEmitterStaticUniformBlock.data[79].y + sysEmitterStaticUniformBlock.data[78].w))))) + 0.5;
    temp_255 = fma(temp_246, NnVfx2ViewParam.data[2].z, fma(temp_248, NnVfx2ViewParam.data[2].y, temp_247 * NnVfx2ViewParam.data[2].x)) + NnVfx2ViewParam.data[2].w;
    temp_256 = fma(temp_246, NnVfx2ViewParam.data[3].z, fma(temp_248, NnVfx2ViewParam.data[3].y, temp_247 * NnVfx2ViewParam.data[3].x)) + NnVfx2ViewParam.data[3].w;
    out_attr1.x = sysEmitterStaticUniformBlock.data[120].x * NnVfx2EmitterDynamicParam.data[1].x * sysEmitterStaticUniformBlock.data[103].x;
    temp_257 = inversesqrt(fma(temp_255, temp_255, fma(temp_254, temp_254, temp_253 * temp_253)));
    temp_258 = fma(temp_256, NnVfx2ViewParam.data[5].w, fma(temp_255, NnVfx2ViewParam.data[5].z, fma(temp_254, NnVfx2ViewParam.data[5].y, temp_253 * NnVfx2ViewParam.data[5].x)));
    gl_Position.y = temp_258;
    temp_259 = fma(temp_256, NnVfx2ViewParam.data[4].w, fma(temp_255, NnVfx2ViewParam.data[4].z, fma(temp_254, NnVfx2ViewParam.data[4].y, temp_253 * NnVfx2ViewParam.data[4].x)));
    temp_260 = 0.0 * temp_258;
    gl_Position.x = temp_259;
    temp_261 = fma(temp_256, NnVfx2ViewParam.data[6].w, fma(temp_255, NnVfx2ViewParam.data[6].z, fma(temp_254, NnVfx2ViewParam.data[6].y, temp_253 * NnVfx2ViewParam.data[6].x)));
    temp_262 = fma(temp_256, NnVfx2ViewParam.data[7].w, fma(temp_255, NnVfx2ViewParam.data[7].z, fma(temp_254, NnVfx2ViewParam.data[7].y, temp_253 * NnVfx2ViewParam.data[7].x)));
    gl_Position.z = temp_261;
    temp_263 = fma(0.0, temp_259, temp_260);
    gl_Position.w = temp_262;
    out_attr2.z = fma(fma(temp_1, sysEmitterStaticUniformBlock.data[79].z, fma(temp_195, sysEmitterStaticUniformBlock.data[80].z, sysEmitterStaticUniformBlock.data[80].x + sysEmitterStaticUniformBlock.data[80].z)), fma(temp_252, temp_137, -0.5), fma(temp_252, float(temp_143 < 0 || !(temp_143 == 0) ? (0 - temp_143 * (temp_229 + (0 - (uint((0 - temp_143 * temp_229)) >= uint(temp_143) ? -1 : 0)))) : -1), fma(temp_1, (0.0 - sysEmitterStaticUniformBlock.data[78].x), (0.0 - fma(temp_189 * sysEmitterStaticUniformBlock.data[79].x, -2.0, sysEmitterStaticUniformBlock.data[79].x + sysEmitterStaticUniformBlock.data[78].z))))) + 0.5;
    out_attr15.x = temp_253 * temp_257;
    temp_264 = temp_262 + fma(0.0, temp_261, temp_263);
    out_attr3.w = temp_264;
    out_attr11.x = sysCustomShaderUniformBlock0.data[36].w;
    out_attr1.y = sysEmitterStaticUniformBlock.data[120].y * NnVfx2EmitterDynamicParam.data[1].y * sysEmitterStaticUniformBlock.data[103].x;
    out_attr1.z = sysEmitterStaticUniformBlock.data[120].z * NnVfx2EmitterDynamicParam.data[1].z * sysEmitterStaticUniformBlock.data[103].x;
    out_attr0.w = fma(temp_162, sysEmitterStaticUniformBlock.data[114].x, fma(fma(((0.0 - sysEmitterStaticUniformBlock.data[113].x) + sysEmitterStaticUniformBlock.data[114].x) * (1.0 / (sysEmitterStaticUniformBlock.data[114].w + (0.0 - sysEmitterStaticUniformBlock.data[113].w))), temp_107 + (0.0 - sysEmitterStaticUniformBlock.data[113].w), sysEmitterStaticUniformBlock.data[113].x), fma(temp_153, (0.0 - temp_162), temp_153), temp_161)) * NnVfx2EmitterDynamicParam.data[0].w;
    out_attr9.y = fma(0.0, temp_134, fma(temp_239, temp_65, fma(temp_237, temp_64, temp_234 * temp_59)));
    out_attr10.x = (0.0 - fma(temp_246, sysCustomShaderUniformBlock0.data[38].z, fma(temp_248, sysCustomShaderUniformBlock0.data[38].y, temp_247 * sysCustomShaderUniformBlock0.data[38].x))) + -0.0;
    out_attr2.x = fma(fma(temp_250, temp_154, -0.5), fma(temp_1, sysEmitterStaticUniformBlock.data[74].z, fma(temp_57, sysEmitterStaticUniformBlock.data[75].z, sysEmitterStaticUniformBlock.data[75].x + sysEmitterStaticUniformBlock.data[75].z)), fma(temp_250, float(temp_139 < 0 || !(temp_139 == 0) ? (0 - temp_139 * (temp_213 + (0 - (uint((0 - temp_139 * temp_213)) >= uint(temp_139) ? -1 : 0)))) : -1), fma(temp_1, (0.0 - sysEmitterStaticUniformBlock.data[73].x), (0.0 - fma(temp_57 * sysEmitterStaticUniformBlock.data[74].x, -2.0, sysEmitterStaticUniformBlock.data[74].x + sysEmitterStaticUniformBlock.data[73].z))))) + 0.5;
    out_attr2.y = fma(fma(temp_1, sysEmitterStaticUniformBlock.data[74].w, fma(temp_108, sysEmitterStaticUniformBlock.data[75].w, sysEmitterStaticUniformBlock.data[75].w + sysEmitterStaticUniformBlock.data[75].y)), fma(temp_249, temp_167, -0.5), (0.0 - fma(temp_249, (0.0 - float(temp_139 < 0 || !(temp_139 == 0) ? (0 - temp_243) + (temp_223 + (0 - (uint((0 - abs(temp_139) * temp_223)) >= uint(abs(temp_139)) ? -1 : 0)) ^ temp_243) : -1)), fma(temp_1, sysEmitterStaticUniformBlock.data[73].y, fma(temp_108 * sysEmitterStaticUniformBlock.data[74].y, -2.0, sysEmitterStaticUniformBlock.data[74].y + sysEmitterStaticUniformBlock.data[73].w))))) + 0.5;
    out_attr15.y = temp_254 * temp_257;
    out_attr15.z = temp_255 * temp_257;
    out_attr3.y = fma(temp_262, 0.5, fma(0.0, temp_261, fma(0.0, temp_259, temp_258 * -0.5)));
    out_attr3.x = fma(temp_262, 0.5, fma(0.0, temp_261, fma(temp_259, 0.5, temp_260)));
    if (0.0 < sysCustomShaderUniformBlock1.data[4].w)
    {
        temp_265 = (0.0 - temp_131) + temp_247;
        temp_266 = (0.0 - temp_134) + temp_248;
        temp_267 = (0.0 - temp_132) + temp_246;
        out_attr13.x = fma(fma(temp_267, NnVfx2ViewParam.data[0].z, fma(temp_266, NnVfx2ViewParam.data[0].y, temp_265 * NnVfx2ViewParam.data[0].x)), sysCustomShaderUniformBlock0.data[31].x, 0.5) * sysCustomShaderUniformBlock0.data[41].x;
        out_attr13.y = fma(fma(temp_267, NnVfx2ViewParam.data[1].z, fma(temp_266, NnVfx2ViewParam.data[1].y, temp_265 * NnVfx2ViewParam.data[1].x)), (0.0 - sysCustomShaderUniformBlock0.data[31].y), 0.5) * sysCustomShaderUniformBlock0.data[41].x;
    }
    out_attr14.x = fma(1.0 / fma(fma(temp_262, 0.5, fma(temp_261, 0.5, temp_263)) * (1.0 / temp_264), NnVfx2ViewParam.data[30].w, (0.0 - NnVfx2ViewParam.data[30].y)), NnVfx2ViewParam.data[30].z, -0.0);
    return;
}
