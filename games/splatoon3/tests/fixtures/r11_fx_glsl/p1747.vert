// static_grsn.bfsha model VfxGeneralShader program 1747 (vert)
// ubo NnVfx2EmitterDynamicParam -> loc 7 (labelled)
// ubo NnVfx2ViewParam -> loc 5 (labelled)
// ubo sysCustomShaderUniformBlock0 -> loc 11
// ubo sysCustomShaderUniformBlock1 -> loc 12
// ubo sysEmitterStaticUniformBlock -> loc 6 (labelled)
// in sysInitRotateAttr -> loc 8
// in sysLocalPosAttr -> loc 4
// in sysLocalVecAttr -> loc 5
// in sysNormalAttr -> loc 2
// in sysPosAttr -> loc 0
// in sysRandomAttr -> loc 7
// in sysScaleAttr -> loc 6
// in sysTangentAttr -> loc 3
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

layout (location = 0) in vec4 sysPosAttr;
layout (location = 1) in vec4 sysTexCoordAttr;
layout (location = 2) in vec4 sysNormalAttr;
layout (location = 3) in vec4 sysTangentAttr;
layout (location = 4) in vec4 sysLocalPosAttr;
layout (location = 5) in vec4 sysLocalVecAttr;
layout (location = 6) in vec4 sysScaleAttr;
layout (location = 7) in vec4 sysRandomAttr;
layout (location = 8) in vec4 sysInitRotateAttr;

layout (location = 0) out vec4 out_attr0;
layout (location = 1) out vec4 out_attr1;
layout (location = 2) out vec4 out_attr2;
layout (location = 3) out vec4 out_attr3;
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
    precise float temp_3;
    bool temp_4;
    precise float temp_5;
    precise float temp_6;
    precise float temp_7;
    int temp_8;
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
    int temp_62;
    precise float temp_63;
    int temp_64;
    int temp_65;
    precise float temp_66;
    precise float temp_67;
    bool temp_68;
    precise float temp_69;
    bool temp_70;
    precise float temp_71;
    precise float temp_72;
    precise float temp_73;
    int temp_74;
    precise float temp_75;
    precise float temp_76;
    precise float temp_77;
    precise float temp_78;
    precise float temp_79;
    precise float temp_80;
    precise float temp_81;
    precise float temp_82;
    int temp_83;
    precise float temp_84;
    bool temp_85;
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
    int temp_105;
    precise float temp_106;
    precise float temp_107;
    int temp_108;
    precise float temp_109;
    precise float temp_110;
    uint temp_111;
    precise float temp_112;
    int temp_113;
    int temp_114;
    precise float temp_115;
    precise float temp_116;
    bool temp_117;
    uint temp_118;
    bool temp_119;
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
    precise float temp_131;
    precise float temp_132;
    precise float temp_133;
    precise float temp_134;
    precise float temp_135;
    precise float temp_136;
    precise float temp_137;
    precise float temp_138;
    bool temp_139;
    int temp_140;
    int temp_141;
    uint temp_142;
    uint temp_143;
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
    int temp_162;
    precise float temp_163;
    precise float temp_164;
    precise float temp_165;
    precise float temp_166;
    int temp_167;
    precise float temp_168;
    precise float temp_169;
    precise float temp_170;
    precise float temp_171;
    precise float temp_172;
    precise float temp_173;
    precise float temp_174;
    precise float temp_175;
    int temp_176;
    int temp_177;
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
    int temp_189;
    precise float temp_190;
    precise float temp_191;
    int temp_192;
    precise float temp_193;
    precise float temp_194;
    precise float temp_195;
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
    precise float temp_206;
    precise float temp_207;
    precise float temp_208;
    gl_PointSize = 1.0;
    gl_Position.x = 0.0;
    gl_Position.y = 0.0;
    gl_Position.z = 0.0;
    gl_Position.w = 1.0;
    temp_0 = sysLocalPosAttr.w;
    temp_1 = sysLocalVecAttr.w;
    temp_2 = (0.0 - temp_1) + NnVfx2EmitterDynamicParam.data[2].x;
    temp_3 = float(int(trunc(temp_0)));
    temp_4 = temp_1 > NnVfx2EmitterDynamicParam.data[2].x || temp_2 >= temp_3;
    temp_5 = temp_1;
    temp_6 = temp_0;
    if (temp_4)
    {
        temp_5 = NnVfx2ViewParam.data[30].y;
    }
    temp_7 = temp_5;
    temp_8 = floatBitsToInt(temp_7);
    if (temp_4)
    {
        gl_Position.x = 0.0;
    }
    if (temp_4)
    {
        temp_8 = floatBitsToInt(temp_7 * 5.0);
    }
    if (temp_4)
    {
        gl_Position.y = 0.0;
    }
    if (temp_4)
    {
        gl_Position.z = intBitsToFloat(temp_8);
    }
    if (temp_4)
    {
        out_attr3.x = 0.0;
    }
    if (temp_4)
    {
        return;
    }
    temp_9 = temp_2 + NnVfx2EmitterDynamicParam.data[2].w;
    temp_10 = sysEmitterStaticUniformBlock.data[14].x == 1.0;
    temp_11 = sysScaleAttr.w;
    if (temp_10)
    {
        temp_6 = temp_9 * temp_9;
    }
    temp_12 = temp_6;
    temp_13 = temp_12;
    if (temp_10)
    {
        temp_13 = temp_12 * sysEmitterStaticUniformBlock.data[13].w;
    }
    temp_14 = temp_13;
    temp_15 = sysRandomAttr.x;
    temp_16 = intBitsToFloat(undef);
    if (temp_10)
    {
        temp_16 = temp_14 * 0.5 * sysEmitterStaticUniformBlock.data[13].y;
    }
    temp_17 = intBitsToFloat(undef);
    temp_18 = temp_16;
    if (temp_10)
    {
        temp_17 = temp_14 * 0.5 * sysEmitterStaticUniformBlock.data[13].z;
    }
    temp_19 = intBitsToFloat(undef);
    temp_20 = temp_17;
    if (temp_10)
    {
        temp_19 = temp_14 * 0.5 * sysEmitterStaticUniformBlock.data[13].x;
    }
    temp_21 = temp_19;
    if (!temp_10)
    {
        temp_22 = 1.0 / log2(sysEmitterStaticUniformBlock.data[14].x) * 1.44269502;
        temp_23 = (temp_9 + (0.0 - fma(temp_22, exp2(temp_9 * log2(abs(sysEmitterStaticUniformBlock.data[14].x))), (0.0 - temp_22)))) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[14].x) + 1.0)) * sysEmitterStaticUniformBlock.data[13].w;
        temp_18 = temp_23 * sysEmitterStaticUniformBlock.data[13].y;
        temp_21 = temp_23 * sysEmitterStaticUniformBlock.data[13].x;
        temp_20 = temp_23 * sysEmitterStaticUniformBlock.data[13].z;
    }
    temp_24 = temp_18;
    temp_25 = temp_21;
    temp_26 = temp_20;
    temp_27 = intBitsToFloat(undef);
    if (temp_10)
    {
        temp_27 = temp_9;
    }
    temp_28 = temp_27;
    if (!temp_10)
    {
        temp_29 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[14].x) + 1.0);
        temp_28 = fma(exp2(temp_9 * log2(abs(sysEmitterStaticUniformBlock.data[14].x))), (0.0 - temp_29), temp_29);
    }
    temp_30 = temp_28;
    temp_31 = fma(fma(temp_30, sysLocalVecAttr.x, fma(temp_26, NnVfx2EmitterDynamicParam.data[10].x, fma(temp_25, NnVfx2EmitterDynamicParam.data[8].x, temp_24 * NnVfx2EmitterDynamicParam.data[9].x))), temp_11, sysLocalPosAttr.x);
    temp_32 = fma(fma(temp_30, sysLocalVecAttr.y, fma(temp_26, NnVfx2EmitterDynamicParam.data[10].y, fma(temp_25, NnVfx2EmitterDynamicParam.data[8].y, temp_24 * NnVfx2EmitterDynamicParam.data[9].y))), temp_11, sysLocalPosAttr.y);
    temp_33 = fma(fma(temp_30, sysLocalVecAttr.z, fma(temp_26, NnVfx2EmitterDynamicParam.data[10].z, fma(temp_25, NnVfx2EmitterDynamicParam.data[8].z, temp_24 * NnVfx2EmitterDynamicParam.data[9].z))), temp_11, sysLocalPosAttr.z);
    if (0.0 < sysEmitterStaticUniformBlock.data[11].x)
    {
        temp_34 = fma(temp_15 * sysEmitterStaticUniformBlock.data[12].y, sysEmitterStaticUniformBlock.data[11].x, temp_2) * (1.0 / sysEmitterStaticUniformBlock.data[11].x);
        temp_35 = temp_34 + (0.0 - floor(temp_34));
    }
    else
    {
        temp_35 = temp_2 * (1.0 / temp_3);
    }
    temp_36 = temp_35;
    temp_37 = temp_36 >= sysEmitterStaticUniformBlock.data[140].w ? 1.0 : 0.0;
    temp_38 = temp_36 >= sysEmitterStaticUniformBlock.data[141].w ? 1.0 : 0.0;
    temp_39 = temp_36 >= sysEmitterStaticUniformBlock.data[142].w ? 1.0 : 0.0;
    temp_40 = fma(temp_37, (0.0 - temp_38), temp_37);
    temp_41 = fma(temp_38, (0.0 - temp_39), temp_38);
    if (0.0 < sysEmitterStaticUniformBlock.data[10].x)
    {
        temp_42 = fma(temp_15 * sysEmitterStaticUniformBlock.data[11].y, sysEmitterStaticUniformBlock.data[10].x, temp_2) * (1.0 / sysEmitterStaticUniformBlock.data[10].x);
        temp_43 = temp_42 + (0.0 - floor(temp_42));
    }
    else
    {
        temp_43 = temp_2 * (1.0 / temp_3);
    }
    temp_44 = temp_43;
    temp_45 = temp_44 + (0.0 - sysEmitterStaticUniformBlock.data[104].w);
    temp_46 = temp_44 >= sysEmitterStaticUniformBlock.data[104].w ? 1.0 : 0.0;
    temp_47 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[104].w) + sysEmitterStaticUniformBlock.data[105].w);
    temp_48 = temp_44 >= sysEmitterStaticUniformBlock.data[105].w ? 1.0 : 0.0;
    temp_49 = fma(temp_46, (0.0 - temp_48), temp_46);
    if (0.0 < sysEmitterStaticUniformBlock.data[10].y)
    {
        temp_50 = fma(temp_15 * sysEmitterStaticUniformBlock.data[11].z, sysEmitterStaticUniformBlock.data[10].y, temp_2) * (1.0 / sysEmitterStaticUniformBlock.data[10].y);
        temp_51 = temp_50 + (0.0 - floor(temp_50));
    }
    else
    {
        temp_51 = temp_2 * (1.0 / temp_3);
    }
    temp_52 = temp_51;
    temp_53 = sysRandomAttr.y;
    temp_54 = sysPosAttr.z;
    temp_55 = sysPosAttr.x;
    temp_56 = sysRandomAttr.z;
    temp_57 = sysPosAttr.y;
    temp_58 = sysTexCoordAttr.x;
    temp_59 = sysNormalAttr.x;
    temp_60 = sysNormalAttr.y;
    temp_61 = sysNormalAttr.z;
    temp_62 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x10000000;
    temp_63 = fma(temp_39, sysEmitterStaticUniformBlock.data[142].z, fma(temp_41, sysEmitterStaticUniformBlock.data[141].z, fma(temp_40, sysEmitterStaticUniformBlock.data[140].z, fma(temp_37, (0.0 - sysEmitterStaticUniformBlock.data[140].z), sysEmitterStaticUniformBlock.data[140].z)))) * sysScaleAttr.z * NnVfx2EmitterDynamicParam.data[3].w * fma(0.5, sysEmitterStaticUniformBlock.data[15].z, temp_54);
    temp_64 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x20000000;
    temp_65 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x40000000;
    temp_66 = (clamp(min(0.0, temp_15) + -0.0, 0.0, 1.0) + sysScaleAttr.x) * fma(temp_39, sysEmitterStaticUniformBlock.data[142].x, fma(temp_41, sysEmitterStaticUniformBlock.data[141].x, fma(temp_40, sysEmitterStaticUniformBlock.data[140].x, fma(temp_37, (0.0 - sysEmitterStaticUniformBlock.data[140].x), sysEmitterStaticUniformBlock.data[140].x)))) * NnVfx2EmitterDynamicParam.data[3].y * fma(0.5, sysEmitterStaticUniformBlock.data[15].x, temp_55);
    temp_67 = fma(temp_39, sysEmitterStaticUniformBlock.data[142].y, fma(temp_41, sysEmitterStaticUniformBlock.data[141].y, fma(temp_40, sysEmitterStaticUniformBlock.data[140].y, fma(temp_37, (0.0 - sysEmitterStaticUniformBlock.data[140].y), sysEmitterStaticUniformBlock.data[140].y)))) * sysScaleAttr.y * NnVfx2EmitterDynamicParam.data[3].z * fma(0.5, sysEmitterStaticUniformBlock.data[15].y, temp_57);
    temp_68 = ((!((1 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 1) || !(temp_15 > 0.5) ? -1 : 0)) != 0;
    temp_69 = floor(temp_15 * 2.0);
    temp_70 = 0.0 == sysEmitterStaticUniformBlock.data[162].w;
    temp_71 = temp_64 >= 0 ? 0.0 : 1.40129846E-45;
    temp_72 = floor(temp_56 * 2.0);
    temp_73 = sysTexCoordAttr.y;
    temp_74 = int(trunc(sysEmitterStaticUniformBlock.data[77].z));
    temp_75 = temp_71;
    temp_76 = temp_73;
    if (!temp_70)
    {
        temp_75 = log2(abs(sysEmitterStaticUniformBlock.data[162].w));
    }
    temp_77 = float(abs((0 - (temp_64 > 0 ? -1 : 0)) + (0 - floatBitsToInt(temp_71))));
    temp_78 = floor(temp_53 * 2.0);
    temp_79 = float(abs((0 - (temp_65 > 0 ? -1 : 0)) + (0 - temp_65 >= 0 ? 0 : 1)));
    temp_80 = intBitsToFloat(undef);
    temp_81 = temp_79;
    temp_82 = temp_77;
    if (!temp_70)
    {
        temp_80 = temp_2 * temp_75;
    }
    temp_83 = int(trunc(sysEmitterStaticUniformBlock.data[82].z));
    temp_84 = temp_58;
    if (!temp_68)
    {
        temp_84 = (0.0 - temp_58) + 1.0;
    }
    temp_85 = sysEmitterStaticUniformBlock.data[162].w == 1.0;
    temp_86 = fma(temp_53 + temp_56, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].y;
    temp_87 = temp_52 >= sysEmitterStaticUniformBlock.data[112].w ? 1.0 : 0.0;
    temp_88 = temp_52 >= sysEmitterStaticUniformBlock.data[113].w ? 1.0 : 0.0;
    temp_89 = fma(temp_86, 2.0, sysEmitterStaticUniformBlock.data[162].y);
    temp_90 = intBitsToFloat(undef);
    temp_91 = temp_86;
    temp_92 = temp_73;
    if (!temp_70)
    {
        temp_90 = temp_80;
    }
    if (!temp_85)
    {
        temp_91 = (0.0 - sysEmitterStaticUniformBlock.data[162].w) + 1.0;
    }
    temp_93 = temp_91;
    temp_94 = intBitsToFloat(undef);
    temp_95 = temp_93;
    if (!temp_70)
    {
        temp_94 = exp2(temp_90);
    }
    temp_96 = temp_58;
    temp_97 = temp_94;
    if (!temp_85)
    {
        temp_95 = 1.0 / temp_93;
    }
    if (!(((!((4 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 4) || !(temp_56 > 0.5) ? -1 : 0)) != 0))
    {
        temp_96 = (0.0 - temp_58) + 1.0;
    }
    temp_98 = fma(fma(temp_15 + temp_53, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].x, 2.0, sysEmitterStaticUniformBlock.data[162].x);
    if (temp_70)
    {
        temp_97 = 1.0;
    }
    temp_99 = fma(temp_15 + temp_56, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].z;
    temp_100 = ((0.0 - temp_72 < 0.0 ? 1.0 : 0.0) + (temp_72 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_62 > 0 ? -1 : 0)) + (0 - temp_62 >= 0 ? 0 : 1)));
    temp_101 = fma(fma((sysEmitterStaticUniformBlock.data[113].x + (0.0 - sysEmitterStaticUniformBlock.data[112].x)) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[112].w) + sysEmitterStaticUniformBlock.data[113].w)), temp_52 + (0.0 - sysEmitterStaticUniformBlock.data[112].w), sysEmitterStaticUniformBlock.data[112].x), fma(temp_88, (0.0 - temp_87), temp_87), fma(temp_87, (0.0 - sysEmitterStaticUniformBlock.data[112].x), sysEmitterStaticUniformBlock.data[112].x));
    temp_102 = temp_52 >= sysEmitterStaticUniformBlock.data[114].w ? 1.0 : 0.0;
    temp_103 = fma(temp_99, 2.0, sysEmitterStaticUniformBlock.data[162].z);
    temp_104 = temp_99;
    temp_105 = 0;
    temp_106 = temp_101;
    if (!temp_85)
    {
        temp_104 = fma(temp_95, (0.0 - temp_97), temp_95);
    }
    temp_107 = sysInitRotateAttr.z;
    temp_108 = floatBitsToInt(1.0 / float(uint(temp_74))) + -2;
    temp_109 = sysInitRotateAttr.x;
    temp_110 = temp_52 >= sysEmitterStaticUniformBlock.data[115].w ? 1.0 : 0.0;
    temp_111 = uint(max(trunc(float(0u) * intBitsToFloat(temp_108)), 0.0));
    temp_112 = temp_104;
    if ((1 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].z)) != 1)
    {
        temp_105 = 1;
    }
    temp_113 = temp_105;
    temp_114 = floatBitsToInt(1.0 / float(uint(temp_83))) + -2;
    temp_115 = sysInitRotateAttr.y;
    if (temp_85)
    {
        temp_112 = temp_2;
    }
    temp_116 = temp_112;
    temp_117 = temp_54 == 0.0 && temp_55 == 0.0 && temp_57 == 0.0;
    if (!(((!((2 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 2) || !(temp_53 > 0.5) ? -1 : 0)) != 0))
    {
        temp_92 = (0.0 - temp_73) + 1.0;
    }
    temp_118 = uint(max(trunc(float(0u) * intBitsToFloat(temp_114)), 0.0));
    temp_119 = temp_113 == 1;
    temp_120 = ((0.0 - temp_69 < 0.0 ? 1.0 : 0.0) + (temp_69 > 0.0 ? 1.0 : 0.0)) * temp_77;
    temp_121 = ((0.0 - temp_78 < 0.0 ? 1.0 : 0.0) + (temp_78 > 0.0 ? 1.0 : 0.0)) * temp_79;
    temp_122 = temp_15;
    temp_123 = temp_53;
    temp_124 = temp_15;
    temp_125 = temp_53;
    if (!(((!((8 & floatBitsToInt(sysEmitterStaticUniformBlock.data[7].y)) == 8) || !(sysRandomAttr.w > 0.5) ? -1 : 0)) != 0))
    {
        temp_76 = (0.0 - temp_73) + 1.0;
    }
    if (temp_117)
    {
        temp_81 = temp_59;
    }
    temp_126 = temp_81;
    if (temp_117)
    {
        temp_82 = temp_60;
    }
    temp_127 = temp_82;
    if (temp_117)
    {
        temp_106 = temp_61;
    }
    temp_128 = temp_106;
    if (temp_119)
    {
        temp_122 = temp_53;
    }
    temp_129 = temp_122;
    temp_130 = temp_129;
    temp_131 = temp_129;
    if (temp_119)
    {
        temp_123 = temp_56;
    }
    temp_132 = temp_123;
    temp_133 = temp_132;
    temp_134 = temp_132;
    if (temp_119)
    {
        temp_124 = temp_53;
    }
    temp_135 = temp_124;
    temp_136 = temp_135;
    temp_137 = temp_135;
    if (temp_119)
    {
        temp_125 = temp_56;
    }
    temp_138 = temp_125;
    if (!temp_119)
    {
        temp_139 = temp_113 == 2;
        if (temp_139)
        {
            temp_130 = temp_56;
        }
        temp_131 = temp_130;
        if (temp_139)
        {
            temp_133 = temp_15;
        }
        temp_134 = temp_133;
        if (temp_139)
        {
            temp_136 = temp_15;
        }
        temp_137 = temp_136;
        if (temp_139)
        {
            temp_138 = temp_53;
        }
    }
    temp_140 = floatBitsToInt(1.0 / float(uint(abs(temp_74)))) + -2;
    temp_141 = floatBitsToInt(1.0 / float(uint(abs(temp_83)))) + -2;
    temp_142 = uint(max(trunc(intBitsToFloat(temp_140) * float(0u)), 0.0));
    temp_143 = uint(max(trunc(float(0u) * intBitsToFloat(temp_141)), 0.0));
    if (!temp_117)
    {
        temp_127 = fma(temp_57, sysEmitterStaticUniformBlock.data[14].y, temp_60);
    }
    temp_144 = temp_127;
    temp_145 = sysTangentAttr.y;
    if (!temp_117)
    {
        temp_128 = fma(temp_54, sysEmitterStaticUniformBlock.data[14].y, temp_61);
    }
    temp_146 = temp_128;
    if (!temp_117)
    {
        temp_126 = fma(temp_55, sysEmitterStaticUniformBlock.data[14].y, temp_59);
    }
    temp_147 = temp_126;
    temp_148 = sysTangentAttr.z;
    temp_149 = sysTangentAttr.x;
    temp_150 = fma(temp_33, NnVfx2EmitterDynamicParam.data[4].z, fma(temp_32, NnVfx2EmitterDynamicParam.data[4].y, temp_31 * NnVfx2EmitterDynamicParam.data[4].x)) + NnVfx2EmitterDynamicParam.data[4].w;
    out_attr11.x = temp_150;
    temp_151 = fma(temp_33, NnVfx2EmitterDynamicParam.data[5].z, fma(temp_32, NnVfx2EmitterDynamicParam.data[5].y, temp_31 * NnVfx2EmitterDynamicParam.data[5].x)) + NnVfx2EmitterDynamicParam.data[5].w;
    out_attr11.y = temp_151;
    temp_152 = fma(temp_33, NnVfx2EmitterDynamicParam.data[6].z, fma(temp_32, NnVfx2EmitterDynamicParam.data[6].y, temp_31 * NnVfx2EmitterDynamicParam.data[6].x)) + NnVfx2EmitterDynamicParam.data[6].w;
    out_attr11.z = temp_152;
    temp_153 = sysTangentAttr.w;
    temp_154 = fma(temp_152, NnVfx2ViewParam.data[11].z, fma(temp_151, NnVfx2ViewParam.data[11].y, temp_150 * NnVfx2ViewParam.data[11].x)) + NnVfx2ViewParam.data[11].w;
    temp_155 = fma(temp_152, NnVfx2ViewParam.data[10].z, fma(temp_151, NnVfx2ViewParam.data[10].y, temp_150 * NnVfx2ViewParam.data[10].x)) + NnVfx2ViewParam.data[10].w;
    temp_156 = fma(fma(temp_98 * temp_100, -2.0, temp_98), temp_116, fma(temp_15 + -0.5, sysEmitterStaticUniformBlock.data[161].x, fma(temp_100 * temp_109, -2.0, temp_109)));
    temp_157 = fma(fma(temp_89 * temp_120, -2.0, temp_89), temp_116, fma(temp_53 + -0.5, sysEmitterStaticUniformBlock.data[161].y, fma(temp_120 * temp_115, -2.0, temp_115)));
    temp_158 = fma(fma(temp_103 * temp_121, -2.0, temp_103), temp_116, fma(temp_56 + -0.5, sysEmitterStaticUniformBlock.data[161].z, fma(temp_121 * temp_107, -2.0, temp_107)));
    temp_159 = fma(temp_60, temp_148, (0.0 - temp_61 * temp_145)) * temp_153;
    temp_160 = fma(temp_61, temp_149, (0.0 - temp_59 * temp_148)) * temp_153;
    temp_161 = fma(temp_59, temp_145, (0.0 - temp_60 * temp_149)) * temp_153;
    temp_162 = int(temp_111) + int(uint(max(trunc(intBitsToFloat(temp_108) * float(uint((0 - temp_74 * int(temp_111))))), 0.0)));
    temp_163 = cos(temp_157) * cos(temp_156);
    temp_164 = sin(temp_156) * sin(temp_157);
    temp_165 = sin(temp_156) * cos(temp_157);
    temp_166 = cos(temp_156) * sin(temp_157);
    temp_167 = int(temp_142) + int(uint(max(trunc(intBitsToFloat(temp_140) * float(uint((0 - abs(temp_74) * int(temp_142))))), 0.0)));
    temp_168 = cos(temp_156) * cos(temp_158);
    temp_169 = cos(temp_158) * sin(temp_157);
    temp_170 = fma(sin(temp_158), temp_163, temp_164);
    temp_171 = fma(sin(temp_158), temp_164, temp_163);
    temp_172 = sin(temp_156) * cos(temp_158);
    temp_173 = fma(sin(temp_158), temp_165, (0.0 - temp_166));
    temp_174 = fma(sin(temp_158), temp_166, (0.0 - temp_165));
    temp_175 = cos(temp_157) * cos(temp_158);
    temp_176 = int(temp_143) + int(uint(max(trunc(intBitsToFloat(temp_141) * float(uint((0 - abs(temp_83) * int(temp_143))))), 0.0)));
    temp_177 = int(temp_118) + int(uint(max(trunc(intBitsToFloat(temp_114) * float(uint((0 - temp_83 * int(temp_118))))), 0.0)));
    temp_178 = clamp(fma(1.0 / fma(fma(temp_155, 0.5, temp_154 * 0.5) * (1.0 / fma(0.0, temp_155, temp_154)), NnVfx2ViewParam.data[30].w, (0.0 - NnVfx2ViewParam.data[30].y)), (0.0 - NnVfx2ViewParam.data[30].z), (0.0 - sysEmitterStaticUniformBlock.data[137].x)) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[137].x) + sysEmitterStaticUniformBlock.data[137].y)), 0.0, 1.0);
    temp_179 = 0.0 + fma(temp_63, temp_169, fma(temp_66, temp_175, sin(temp_158) * (0.0 - temp_67)));
    temp_180 = 0.0 + fma(temp_169, temp_148, fma(temp_175, temp_149, sin(temp_158) * (0.0 - temp_145)));
    temp_181 = 0.0 + fma(temp_174, temp_63, fma(temp_170, temp_66, temp_67 * temp_168));
    temp_182 = 0.0 + fma(temp_174, temp_148, fma(temp_170, temp_149, temp_168 * temp_145));
    temp_183 = 0.0 + fma(temp_169, temp_146, fma(temp_175, temp_147, sin(temp_158) * (0.0 - temp_144)));
    temp_184 = 0.0 + fma(temp_169, temp_161, fma(temp_175, temp_159, sin(temp_158) * (0.0 - temp_160)));
    temp_185 = 0.0 + fma(temp_174, temp_161, fma(temp_170, temp_159, temp_168 * temp_160));
    temp_186 = 0.0 + fma(temp_174, temp_146, fma(temp_170, temp_147, temp_168 * temp_144));
    temp_187 = 0.0 + fma(temp_171, temp_63, fma(temp_173, temp_66, temp_67 * temp_172));
    temp_188 = 0.0 + fma(temp_171, temp_148, fma(temp_173, temp_149, temp_172 * temp_145));
    temp_189 = (0 - int(uint(temp_74) >> 31));
    temp_190 = 0.0 + fma(temp_171, temp_161, fma(temp_173, temp_159, temp_172 * temp_160));
    temp_191 = 0.0 + fma(temp_171, temp_146, fma(temp_173, temp_147, temp_172 * temp_144));
    temp_192 = (0 - int(uint(temp_83) >> 31));
    temp_193 = fma(0.0, temp_63, fma(0.0, temp_66, 0.0 * temp_67)) + 1.0;
    temp_194 = fma(temp_151, temp_193, fma(temp_187, NnVfx2EmitterDynamicParam.data[9].z, fma(temp_181, NnVfx2EmitterDynamicParam.data[9].y, temp_179 * NnVfx2EmitterDynamicParam.data[9].x)));
    out_attr5.y = temp_194;
    temp_195 = fma(temp_152, temp_193, fma(temp_187, NnVfx2EmitterDynamicParam.data[10].z, fma(temp_181, NnVfx2EmitterDynamicParam.data[10].y, temp_179 * NnVfx2EmitterDynamicParam.data[10].x)));
    temp_196 = fma(temp_150, temp_193, fma(temp_187, NnVfx2EmitterDynamicParam.data[8].z, fma(temp_181, NnVfx2EmitterDynamicParam.data[8].y, temp_179 * NnVfx2EmitterDynamicParam.data[8].x)));
    out_attr5.z = temp_195;
    out_attr5.x = temp_196;
    out_attr0.x = fma(temp_48, sysEmitterStaticUniformBlock.data[105].x, fma(fma(temp_45, (sysEmitterStaticUniformBlock.data[105].x + (0.0 - sysEmitterStaticUniformBlock.data[104].x)) * temp_47, sysEmitterStaticUniformBlock.data[104].x), temp_49, fma(temp_46, (0.0 - sysEmitterStaticUniformBlock.data[104].x), sysEmitterStaticUniformBlock.data[104].x))) * NnVfx2EmitterDynamicParam.data[0].x * sysEmitterStaticUniformBlock.data[103].x;
    out_attr0.y = fma(temp_48, sysEmitterStaticUniformBlock.data[105].y, fma(fma(temp_45, (sysEmitterStaticUniformBlock.data[105].y + (0.0 - sysEmitterStaticUniformBlock.data[104].y)) * temp_47, sysEmitterStaticUniformBlock.data[104].y), temp_49, fma(temp_46, (0.0 - sysEmitterStaticUniformBlock.data[104].y), sysEmitterStaticUniformBlock.data[104].y))) * NnVfx2EmitterDynamicParam.data[0].y * sysEmitterStaticUniformBlock.data[103].x;
    temp_197 = 1.0 / sysEmitterStaticUniformBlock.data[77].w * sysEmitterStaticUniformBlock.data[77].y;
    out_attr1.x = sysEmitterStaticUniformBlock.data[120].x * NnVfx2EmitterDynamicParam.data[1].x * sysEmitterStaticUniformBlock.data[103].x;
    temp_198 = 1.0 / sysEmitterStaticUniformBlock.data[77].z * sysEmitterStaticUniformBlock.data[77].x;
    out_attr0.z = fma(temp_48, sysEmitterStaticUniformBlock.data[105].z, fma(fma(temp_45, (sysEmitterStaticUniformBlock.data[105].z + (0.0 - sysEmitterStaticUniformBlock.data[104].z)) * temp_47, sysEmitterStaticUniformBlock.data[104].z), temp_49, fma(temp_46, (0.0 - sysEmitterStaticUniformBlock.data[104].z), sysEmitterStaticUniformBlock.data[104].z))) * NnVfx2EmitterDynamicParam.data[0].z * sysEmitterStaticUniformBlock.data[103].x;
    temp_199 = 1.0 / sysEmitterStaticUniformBlock.data[82].w * sysEmitterStaticUniformBlock.data[82].y;
    out_attr7.z = fma(0.0, temp_152, fma(temp_188, NnVfx2EmitterDynamicParam.data[10].z, fma(temp_182, NnVfx2EmitterDynamicParam.data[10].y, temp_180 * NnVfx2EmitterDynamicParam.data[10].x)));
    temp_200 = 1.0 / sysEmitterStaticUniformBlock.data[82].z * sysEmitterStaticUniformBlock.data[82].x;
    out_attr7.y = fma(0.0, temp_151, fma(temp_188, NnVfx2EmitterDynamicParam.data[9].z, fma(temp_182, NnVfx2EmitterDynamicParam.data[9].y, temp_180 * NnVfx2EmitterDynamicParam.data[9].x)));
    out_attr7.x = fma(0.0, temp_150, fma(temp_188, NnVfx2EmitterDynamicParam.data[8].z, fma(temp_182, NnVfx2EmitterDynamicParam.data[8].y, temp_180 * NnVfx2EmitterDynamicParam.data[8].x)));
    out_attr8.y = fma(0.0, temp_151, fma(temp_190, NnVfx2EmitterDynamicParam.data[9].z, fma(temp_185, NnVfx2EmitterDynamicParam.data[9].y, temp_184 * NnVfx2EmitterDynamicParam.data[9].x)));
    out_attr8.z = fma(0.0, temp_152, fma(temp_190, NnVfx2EmitterDynamicParam.data[10].z, fma(temp_185, NnVfx2EmitterDynamicParam.data[10].y, temp_184 * NnVfx2EmitterDynamicParam.data[10].x)));
    out_attr8.x = fma(0.0, temp_150, fma(temp_190, NnVfx2EmitterDynamicParam.data[8].z, fma(temp_185, NnVfx2EmitterDynamicParam.data[8].y, temp_184 * NnVfx2EmitterDynamicParam.data[8].x)));
    temp_201 = fma(temp_195, NnVfx2ViewParam.data[0].z, fma(temp_194, NnVfx2ViewParam.data[0].y, temp_196 * NnVfx2ViewParam.data[0].x)) + NnVfx2ViewParam.data[0].w;
    out_attr6.z = fma(0.0, temp_152, fma(temp_191, NnVfx2EmitterDynamicParam.data[10].z, fma(temp_186, NnVfx2EmitterDynamicParam.data[10].y, temp_183 * NnVfx2EmitterDynamicParam.data[10].x)));
    temp_202 = fma(temp_195, NnVfx2ViewParam.data[1].z, fma(temp_194, NnVfx2ViewParam.data[1].y, temp_196 * NnVfx2ViewParam.data[1].x)) + NnVfx2ViewParam.data[1].w;
    out_attr6.y = fma(0.0, temp_151, fma(temp_191, NnVfx2EmitterDynamicParam.data[9].z, fma(temp_186, NnVfx2EmitterDynamicParam.data[9].y, temp_183 * NnVfx2EmitterDynamicParam.data[9].x)));
    temp_203 = fma(temp_195, NnVfx2ViewParam.data[2].z, fma(temp_194, NnVfx2ViewParam.data[2].y, temp_196 * NnVfx2ViewParam.data[2].x)) + NnVfx2ViewParam.data[2].w;
    out_attr9.x = (0.0 - fma(temp_195, sysCustomShaderUniformBlock0.data[38].z, fma(temp_194, sysCustomShaderUniformBlock0.data[38].y, temp_196 * sysCustomShaderUniformBlock0.data[38].x))) + -0.0;
    temp_204 = inversesqrt(fma(temp_203, temp_203, fma(temp_202, temp_202, temp_201 * temp_201)));
    out_attr2.z = fma(fma(temp_2, sysEmitterStaticUniformBlock.data[79].z, fma(temp_137, sysEmitterStaticUniformBlock.data[80].z, sysEmitterStaticUniformBlock.data[80].x + sysEmitterStaticUniformBlock.data[80].z)), fma(temp_200, temp_96, -0.5), fma(temp_200, float(temp_83 < 0 || !(temp_83 == 0) ? (0 - temp_83 * (temp_177 + (0 - (uint((0 - temp_83 * temp_177)) >= uint(temp_83) ? -1 : 0)))) : -1), fma(temp_2, (0.0 - sysEmitterStaticUniformBlock.data[78].x), (0.0 - fma(temp_131 * sysEmitterStaticUniformBlock.data[79].x, -2.0, sysEmitterStaticUniformBlock.data[79].x + sysEmitterStaticUniformBlock.data[78].z))))) + 0.5;
    out_attr2.w = fma(fma(temp_2, sysEmitterStaticUniformBlock.data[79].w, fma(temp_138, sysEmitterStaticUniformBlock.data[80].w, sysEmitterStaticUniformBlock.data[80].w + sysEmitterStaticUniformBlock.data[80].y)), fma(temp_199, temp_76, -0.5), (0.0 - fma(temp_199, (0.0 - float(temp_83 < 0 || !(temp_83 == 0) ? (0 - temp_192) + (temp_176 + (0 - (uint((0 - abs(temp_83) * temp_176)) >= uint(abs(temp_83)) ? -1 : 0)) ^ temp_192) : -1)), fma(temp_2, sysEmitterStaticUniformBlock.data[78].y, fma(temp_134 * sysEmitterStaticUniformBlock.data[79].y, -2.0, sysEmitterStaticUniformBlock.data[79].y + sysEmitterStaticUniformBlock.data[78].w))))) + 0.5;
    temp_205 = fma(temp_195, NnVfx2ViewParam.data[3].z, fma(temp_194, NnVfx2ViewParam.data[3].y, temp_196 * NnVfx2ViewParam.data[3].x)) + NnVfx2ViewParam.data[3].w;
    out_attr1.y = sysEmitterStaticUniformBlock.data[120].y * NnVfx2EmitterDynamicParam.data[1].y * sysEmitterStaticUniformBlock.data[103].x;
    out_attr10.x = sysCustomShaderUniformBlock0.data[36].w;
    out_attr1.z = sysEmitterStaticUniformBlock.data[120].z * NnVfx2EmitterDynamicParam.data[1].z * sysEmitterStaticUniformBlock.data[103].x;
    out_attr0.w = fma(temp_110, sysEmitterStaticUniformBlock.data[115].x, fma(fma((sysEmitterStaticUniformBlock.data[115].x + (0.0 - sysEmitterStaticUniformBlock.data[114].x)) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[114].w) + sysEmitterStaticUniformBlock.data[115].w)), temp_52 + (0.0 - sysEmitterStaticUniformBlock.data[114].w), sysEmitterStaticUniformBlock.data[114].x), fma(temp_102, (0.0 - temp_110), temp_102), fma(fma(((0.0 - sysEmitterStaticUniformBlock.data[113].x) + sysEmitterStaticUniformBlock.data[114].x) * (1.0 / (sysEmitterStaticUniformBlock.data[114].w + (0.0 - sysEmitterStaticUniformBlock.data[113].w))), temp_52 + (0.0 - sysEmitterStaticUniformBlock.data[113].w), sysEmitterStaticUniformBlock.data[113].x), fma(temp_88, (0.0 - temp_102), temp_88), temp_101))) * NnVfx2EmitterDynamicParam.data[0].w;
    out_attr3.x = temp_178 * NnVfx2EmitterDynamicParam.data[3].x;
    out_attr6.x = fma(0.0, temp_150, fma(temp_191, NnVfx2EmitterDynamicParam.data[8].z, fma(temp_186, NnVfx2EmitterDynamicParam.data[8].y, temp_183 * NnVfx2EmitterDynamicParam.data[8].x)));
    out_attr2.x = fma(fma(temp_198, temp_84, -0.5), fma(temp_2, sysEmitterStaticUniformBlock.data[74].z, fma(temp_15, sysEmitterStaticUniformBlock.data[75].z, sysEmitterStaticUniformBlock.data[75].x + sysEmitterStaticUniformBlock.data[75].z)), fma(temp_198, float(temp_74 < 0 || !(temp_74 == 0) ? (0 - temp_74 * (temp_162 + (0 - (uint((0 - temp_74 * temp_162)) >= uint(temp_74) ? -1 : 0)))) : -1), fma(temp_2, (0.0 - sysEmitterStaticUniformBlock.data[73].x), (0.0 - fma(temp_15 * sysEmitterStaticUniformBlock.data[74].x, -2.0, sysEmitterStaticUniformBlock.data[74].x + sysEmitterStaticUniformBlock.data[73].z))))) + 0.5;
    out_attr2.y = fma(fma(temp_2, sysEmitterStaticUniformBlock.data[74].w, fma(temp_53, sysEmitterStaticUniformBlock.data[75].w, sysEmitterStaticUniformBlock.data[75].w + sysEmitterStaticUniformBlock.data[75].y)), fma(temp_197, temp_92, -0.5), (0.0 - fma(temp_197, (0.0 - float(temp_74 < 0 || !(temp_74 == 0) ? (0 - temp_189) + (temp_167 + (0 - (uint((0 - abs(temp_74) * temp_167)) >= uint(abs(temp_74)) ? -1 : 0)) ^ temp_189) : -1)), fma(temp_2, sysEmitterStaticUniformBlock.data[73].y, fma(temp_53 * sysEmitterStaticUniformBlock.data[74].y, -2.0, sysEmitterStaticUniformBlock.data[74].y + sysEmitterStaticUniformBlock.data[73].w))))) + 0.5;
    gl_Position.z = fma(temp_205, NnVfx2ViewParam.data[6].w, fma(temp_203, NnVfx2ViewParam.data[6].z, fma(temp_202, NnVfx2ViewParam.data[6].y, temp_201 * NnVfx2ViewParam.data[6].x)));
    gl_Position.x = fma(temp_205, NnVfx2ViewParam.data[4].w, fma(temp_203, NnVfx2ViewParam.data[4].z, fma(temp_202, NnVfx2ViewParam.data[4].y, temp_201 * NnVfx2ViewParam.data[4].x)));
    gl_Position.w = fma(temp_205, NnVfx2ViewParam.data[7].w, fma(temp_203, NnVfx2ViewParam.data[7].z, fma(temp_202, NnVfx2ViewParam.data[7].y, temp_201 * NnVfx2ViewParam.data[7].x)));
    gl_Position.y = fma(temp_205, NnVfx2ViewParam.data[5].w, fma(temp_203, NnVfx2ViewParam.data[5].z, fma(temp_202, NnVfx2ViewParam.data[5].y, temp_201 * NnVfx2ViewParam.data[5].x)));
    out_attr13.x = temp_201 * temp_204;
    out_attr13.y = temp_202 * temp_204;
    if (0.0 < sysCustomShaderUniformBlock1.data[4].w)
    {
        temp_206 = (0.0 - temp_150) + temp_196;
        temp_207 = (0.0 - temp_151) + temp_194;
        temp_208 = (0.0 - temp_152) + temp_195;
        out_attr12.x = fma(fma(temp_208, NnVfx2ViewParam.data[0].z, fma(temp_207, NnVfx2ViewParam.data[0].y, temp_206 * NnVfx2ViewParam.data[0].x)), sysCustomShaderUniformBlock0.data[31].x, 0.5) * sysCustomShaderUniformBlock0.data[41].x;
        out_attr12.y = fma(fma(temp_208, NnVfx2ViewParam.data[1].z, fma(temp_207, NnVfx2ViewParam.data[1].y, temp_206 * NnVfx2ViewParam.data[1].x)), (0.0 - sysCustomShaderUniformBlock0.data[31].y), 0.5) * sysCustomShaderUniformBlock0.data[41].x;
    }
    out_attr13.z = temp_203 * temp_204;
    if (!(temp_178 <= 0.0))
    {
        return;
    }
    gl_Position.x = 0.0;
    gl_Position.y = 0.0;
    gl_Position.z = NnVfx2ViewParam.data[30].y * 5.0;
    out_attr3.x = 0.0;
    return;
}
