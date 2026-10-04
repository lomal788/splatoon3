// static_grsn.bfsha model VfxGeneralShader program 1385 (vert)
// sampler sysTextureSampler2 -> loc 2 -> material sampler ?
// ubo NnVfx2EmitterDynamicParam -> loc 7 (labelled)
// ubo NnVfx2ViewParam -> loc 5 (labelled)
// ubo sysCustomShaderUniformBlock0 -> loc 11
// ubo sysCustomShaderUniformBlock1 -> loc 12
// ubo sysEmitterStaticUniformBlock -> loc 6 (labelled)
// in sysInitRotateAttr -> loc 5
// in sysLocalPosAttr -> loc 1
// in sysLocalVecAttr -> loc 2
// in sysRandomAttr -> loc 4
// in sysScaleAttr -> loc 3
// in sysTexCoordAttr -> loc 0
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

layout (binding = 15, std140) uniform _sysCustomShaderUniformBlock1
{
    precise vec4 data[4096];
} sysCustomShaderUniformBlock1;

layout (binding = 1, std140) uniform _vp_c1
{
    precise vec4 data[4096];
} vp_c1;

layout (binding = 14, std140) uniform _sysCustomShaderUniformBlock0
{
    precise vec4 data[4096];
} sysCustomShaderUniformBlock0;

layout (binding = 0) uniform sampler2D sysTextureSampler2;
layout (location = 0) in vec4 sysTexCoordAttr;
layout (location = 1) in vec4 sysLocalPosAttr;
layout (location = 2) in vec4 sysLocalVecAttr;
layout (location = 3) in vec4 sysScaleAttr;
layout (location = 4) in vec4 sysRandomAttr;
layout (location = 5) in vec4 sysInitRotateAttr;

layout (location = 0) out vec4 out_attr0;
layout (location = 1) out vec4 out_attr1;
layout (location = 3) out vec4 out_attr3;
layout (location = 4) out vec4 out_attr4;
layout (location = 5) out vec4 out_attr5;
layout (location = 6) out vec4 out_attr6;
layout (location = 7) out vec4 out_attr7;
layout (location = 8) out vec4 out_attr8;
layout (location = 9) out vec4 out_attr9;

int TextureSizeUnscale(int a0, int a1);
int TexelFetchScale(int a0, int a1);

int TextureSizeUnscale(int a0, int a1)
{
    precise float temp_0;
    temp_0 = abs(support_buffer.render_scale[1 + a1 + support_buffer.frag_scale_count]);
    if (temp_0 == 1.0)
    {
        return a0;
    }
    return int(float(a0) / temp_0);
}

int TexelFetchScale(int a0, int a1)
{
    precise float temp_1;
    temp_1 = support_buffer.render_scale[1 + a1 + support_buffer.frag_scale_count];
    if (temp_1 == 1.0)
    {
        return a0;
    }
    return int(float(a0) * temp_1);
}

void main()
{
    precise float temp_2;
    precise float temp_3;
    precise float temp_4;
    bool temp_5;
    precise float temp_6;
    precise float temp_7;
    precise float temp_8;
    int temp_9;
    precise float temp_10;
    precise float temp_11;
    precise float temp_12;
    precise float temp_13;
    int temp_14;
    precise float temp_15;
    precise float temp_16;
    precise float temp_17;
    int temp_18;
    precise vec4 temp_19;
    precise float temp_20;
    precise float temp_21;
    precise float temp_22;
    precise float temp_23;
    precise float temp_24;
    int temp_25;
    precise float temp_26;
    precise vec4 temp_27;
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
    int temp_38;
    bool temp_39;
    bool temp_40;
    precise float temp_41;
    int temp_42;
    precise float temp_43;
    precise float temp_44;
    int temp_45;
    int temp_46;
    int temp_47;
    int temp_48;
    int temp_49;
    bool temp_50;
    precise float temp_51;
    precise float temp_52;
    precise float temp_53;
    int temp_54;
    precise float temp_55;
    precise float temp_56;
    precise float temp_57;
    precise float temp_58;
    int temp_59;
    precise float temp_60;
    bool temp_61;
    int temp_62;
    bool temp_63;
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
    bool temp_87;
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
    int temp_111;
    precise float temp_112;
    precise float temp_113;
    precise float temp_114;
    precise float temp_115;
    precise float temp_116;
    int temp_117;
    int temp_118;
    bool temp_119;
    int temp_120;
    int temp_121;
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
    gl_PointSize = 1.0;
    gl_Position.x = 0.0;
    gl_Position.y = 0.0;
    gl_Position.z = 0.0;
    gl_Position.w = 1.0;
    temp_2 = sysLocalVecAttr.w;
    temp_3 = (0.0 - temp_2) + NnVfx2EmitterDynamicParam.data[2].x;
    temp_4 = float(int(trunc(sysLocalPosAttr.w)));
    temp_5 = temp_2 > NnVfx2EmitterDynamicParam.data[2].x || temp_3 >= temp_4;
    temp_6 = temp_2;
    temp_7 = temp_3;
    if (temp_5)
    {
        temp_6 = NnVfx2ViewParam.data[30].y;
    }
    temp_8 = temp_6;
    temp_9 = floatBitsToInt(temp_8);
    if (temp_5)
    {
        gl_Position.x = 0.0;
    }
    if (temp_5)
    {
        temp_9 = floatBitsToInt(temp_8 * 5.0);
    }
    if (temp_5)
    {
        gl_Position.y = 0.0;
    }
    if (temp_5)
    {
        gl_Position.z = intBitsToFloat(temp_9);
    }
    if (temp_5)
    {
        out_attr1.x = 0.0;
    }
    if (temp_5)
    {
        return;
    }
    temp_10 = sysRandomAttr.x;
    if (0.0 < sysEmitterStaticUniformBlock.data[11].x)
    {
        temp_11 = fma(temp_10 * sysEmitterStaticUniformBlock.data[12].y, sysEmitterStaticUniformBlock.data[11].x, temp_3) * (1.0 / sysEmitterStaticUniformBlock.data[11].x);
        temp_12 = temp_11 + (0.0 - floor(temp_11));
    }
    else
    {
        temp_12 = temp_3 * (1.0 / temp_4);
    }
    temp_13 = temp_12;
    temp_14 = int(trunc(sysTexCoordAttr.z));
    temp_15 = float(TextureSizeUnscale(textureSize(sysTextureSampler2, 0).r, 0));
    temp_16 = clamp(min(fma(1.0 / (temp_15 + 9.99999975E-06), temp_3 * sysCustomShaderUniformBlock1.data[12].x, 1E-05), 0.99999) + -0.0, 0.0, 1.0);
    temp_17 = temp_15 * (temp_16 + (0.0 - floor(temp_16)));
    temp_18 = int(trunc(temp_17));
    temp_19 = texelFetch(sysTextureSampler2, ivec2(TexelFetchScale(temp_18, 0), TexelFetchScale(temp_14, 0)), 0).xyzw;
    temp_20 = temp_19.x;
    temp_21 = temp_19.y;
    temp_22 = temp_19.z;
    temp_23 = temp_19.w;
    temp_24 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[140].w) + sysEmitterStaticUniformBlock.data[141].w);
    temp_25 = temp_18;
    temp_26 = temp_23;
    if (temp_18 < int(trunc(temp_15 + -1.0)))
    {
        temp_25 = temp_18 + 1;
    }
    temp_27 = texelFetch(sysTextureSampler2, ivec2(TexelFetchScale(temp_25, 0), TexelFetchScale(temp_14, 0)), 0).xyzw;
    temp_28 = temp_27.w;
    temp_29 = 1.0 / (sysEmitterStaticUniformBlock.data[142].w + (0.0 - sysEmitterStaticUniformBlock.data[141].w));
    temp_30 = temp_13 >= sysEmitterStaticUniformBlock.data[140].w ? 1.0 : 0.0;
    temp_31 = temp_13 + (0.0 - sysEmitterStaticUniformBlock.data[140].w);
    temp_32 = temp_13 >= sysEmitterStaticUniformBlock.data[141].w ? 1.0 : 0.0;
    temp_33 = temp_13 + (0.0 - sysEmitterStaticUniformBlock.data[141].w);
    temp_34 = temp_13 >= sysEmitterStaticUniformBlock.data[142].w ? 1.0 : 0.0;
    temp_35 = fma(temp_30, (0.0 - temp_32), temp_30);
    temp_36 = fma(temp_32, (0.0 - temp_34), temp_32);
    temp_37 = sysRandomAttr.z;
    temp_38 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x20000000;
    temp_39 = temp_38 > 0;
    temp_40 = temp_23 < 0.0;
    temp_41 = temp_30;
    temp_42 = (temp_39 ? -1 : 0);
    temp_43 = sysEmitterStaticUniformBlock.data[162].w;
    if (temp_40)
    {
        temp_26 = (0.0 - temp_23) + -0.0;
    }
    temp_44 = temp_26;
    temp_45 = int(trunc(log2(temp_44)));
    temp_46 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x10000000;
    temp_47 = temp_45;
    if (log2(temp_44) < 0.0)
    {
        temp_47 = temp_45 + -1;
    }
    temp_48 = temp_47;
    temp_49 = 0;
    if (temp_40)
    {
        temp_49 = 0x8000;
    }
    temp_50 = 0.0 == sysEmitterStaticUniformBlock.data[162].w;
    if (!temp_50)
    {
        temp_41 = log2(abs(sysEmitterStaticUniformBlock.data[162].w));
    }
    temp_51 = floor(temp_10 * 2.0);
    temp_52 = intBitsToFloat(undef);
    if (!temp_50)
    {
        temp_52 = temp_3 * temp_41;
    }
    temp_53 = sysInitRotateAttr.y;
    temp_54 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x40000000;
    temp_55 = sysRandomAttr.y;
    temp_56 = temp_51 > 0.0 ? 1.0 : 0.0;
    temp_57 = intBitsToFloat(undef);
    temp_58 = temp_56;
    if (!temp_50)
    {
        temp_57 = temp_52;
    }
    temp_59 = (temp_48 + 15 << 10) + int(trunc(fma(exp2(float((0 - temp_48))) * temp_44, 1024.0, -1024.0))) + temp_49;
    temp_60 = floor(temp_37 * 2.0);
    temp_61 = temp_59 < 0x8000;
    if (temp_61)
    {
        temp_42 = temp_59 + 0xFFFFFC00;
    }
    temp_62 = temp_42;
    if (!temp_61)
    {
        temp_62 = (0 - temp_59) + 0x8400;
    }
    temp_63 = sysEmitterStaticUniformBlock.data[162].w == 1.0;
    temp_64 = sysInitRotateAttr.x;
    temp_65 = float(temp_62 + 0x77FF);
    if (!temp_50)
    {
        temp_58 = exp2(temp_57);
    }
    temp_66 = floor(temp_55 * 2.0);
    temp_67 = temp_58;
    if (temp_50)
    {
        temp_67 = 1.0;
    }
    if (!temp_63)
    {
        temp_43 = (0.0 - sysEmitterStaticUniformBlock.data[162].w) + 1.0;
    }
    temp_68 = temp_43;
    temp_69 = temp_68;
    if (!temp_63)
    {
        temp_69 = 1.0 / temp_68;
    }
    temp_70 = sysInitRotateAttr.z;
    temp_71 = ((0.0 - temp_60 < 0.0 ? 1.0 : 0.0) + (temp_60 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_46 > 0 ? -1 : 0)) + (0 - temp_46 >= 0 ? 0 : 1)));
    temp_72 = fma(fma(temp_10 + temp_55, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].x, 2.0, sysEmitterStaticUniformBlock.data[162].x);
    temp_73 = fma(fma(temp_55 + temp_37, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].y, 2.0, sysEmitterStaticUniformBlock.data[162].y);
    temp_74 = fma(fma(temp_10 + temp_37, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].z, 2.0, sysEmitterStaticUniformBlock.data[162].z);
    temp_75 = ((0.0 - temp_51 < 0.0 ? 1.0 : 0.0) + temp_56) * float(abs((0 - (temp_39 ? -1 : 0)) + (0 - temp_38 >= 0 ? 0 : 1)));
    temp_76 = fma(temp_65 * 2.0, -1.6276572E-05, 0.999983728);
    if (!temp_63)
    {
        temp_7 = fma(temp_69, (0.0 - temp_67), temp_69);
    }
    temp_77 = temp_7;
    temp_78 = abs(temp_76) + -0.0;
    temp_79 = ((0.0 - temp_66 < 0.0 ? 1.0 : 0.0) + (temp_66 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_54 > 0 ? -1 : 0)) + (0 - temp_54 >= 0 ? 0 : 1)));
    temp_80 = sysLocalPosAttr.y;
    temp_81 = temp_76 < 0.0 ? 1.0 : 0.0;
    temp_82 = fma(fma(temp_72 * temp_71, -2.0, temp_72), temp_77, fma(temp_10 + -0.5, sysEmitterStaticUniformBlock.data[161].x, fma(temp_71 * temp_64, -2.0, temp_64)));
    temp_83 = fma(fma(temp_73 * temp_75, -2.0, temp_73), temp_77, fma(temp_55 + -0.5, sysEmitterStaticUniformBlock.data[161].y, fma(temp_75 * temp_53, -2.0, temp_53)));
    temp_84 = fma(fma(fma(temp_78, -0.0187293, 0.0742610022), temp_78, -0.2121144), temp_78, 1.5707288) * sqrt((0.0 - abs(temp_76)) + 1.0);
    temp_85 = temp_65 * 3.88322115;
    temp_86 = fma(fma(temp_74 * temp_79, -2.0, temp_74), temp_77, fma(temp_37 + -0.5, sysEmitterStaticUniformBlock.data[161].z, fma(temp_79 * temp_70, -2.0, temp_70)));
    temp_87 = temp_28 < 0.0;
    temp_88 = sin(temp_82) * cos(temp_83);
    temp_89 = sin(temp_82) * sin(temp_83);
    temp_90 = sin(temp_83) * cos(temp_82);
    temp_91 = sin(temp_82) * cos(temp_86);
    temp_92 = sin(fma(temp_81, 3.1415927, fma(temp_84 * temp_81, -2.0, temp_84)));
    temp_93 = cos(temp_83) * cos(temp_82);
    temp_94 = cos(temp_83) * cos(temp_86);
    temp_95 = cos(temp_86) * cos(temp_82);
    temp_96 = sin(temp_83) * cos(temp_86);
    temp_97 = temp_17 + (0.0 - floor(temp_17));
    temp_98 = fma(sin(temp_86), temp_93, temp_89);
    temp_99 = fma(sin(temp_86), temp_89, temp_93);
    temp_100 = sysLocalPosAttr.x;
    temp_101 = temp_28;
    if (temp_87)
    {
        temp_101 = (0.0 - temp_28) + -0.0;
    }
    temp_102 = temp_101;
    temp_103 = fma(sin(temp_86), temp_88, (0.0 - temp_90));
    temp_104 = fma(sin(temp_86), temp_90, (0.0 - temp_88));
    temp_105 = temp_92 * sin(temp_85);
    temp_106 = sysLocalPosAttr.z;
    temp_107 = temp_92 * cos(temp_85);
    temp_108 = fma((0.0 - temp_22) + temp_27.z, temp_97, temp_22);
    temp_109 = int(trunc(log2(temp_102)));
    temp_110 = temp_109;
    if (log2(temp_102) < 0.0)
    {
        temp_110 = temp_109 + -1;
    }
    temp_111 = temp_110;
    temp_112 = fma(temp_106, NnVfx2EmitterDynamicParam.data[6].z, fma(temp_80, NnVfx2EmitterDynamicParam.data[6].y, temp_100 * NnVfx2EmitterDynamicParam.data[6].x)) + NnVfx2EmitterDynamicParam.data[6].w;
    temp_113 = fma(temp_106, NnVfx2EmitterDynamicParam.data[5].z, fma(temp_80, NnVfx2EmitterDynamicParam.data[5].y, temp_100 * NnVfx2EmitterDynamicParam.data[5].x)) + NnVfx2EmitterDynamicParam.data[5].w;
    out_attr7.z = temp_112;
    temp_114 = fma(temp_106, NnVfx2EmitterDynamicParam.data[4].z, fma(temp_80, NnVfx2EmitterDynamicParam.data[4].y, temp_100 * NnVfx2EmitterDynamicParam.data[4].x)) + NnVfx2EmitterDynamicParam.data[4].w;
    out_attr7.y = temp_113;
    out_attr7.x = temp_114;
    temp_115 = fma(temp_112, NnVfx2ViewParam.data[11].z, fma(temp_113, NnVfx2ViewParam.data[11].y, temp_114 * NnVfx2ViewParam.data[11].x)) + NnVfx2ViewParam.data[11].w;
    temp_116 = fma(temp_112, NnVfx2ViewParam.data[10].z, fma(temp_113, NnVfx2ViewParam.data[10].y, temp_114 * NnVfx2ViewParam.data[10].x)) + NnVfx2ViewParam.data[10].w;
    temp_117 = 0;
    if (temp_87)
    {
        temp_117 = 0x8000;
    }
    temp_118 = (temp_111 + 15 << 10) + int(trunc(fma(exp2(float((0 - temp_111))) * temp_102, 1024.0, -1024.0))) + temp_117;
    temp_119 = temp_118 < 0x8000;
    out_attr0.w = sysEmitterStaticUniformBlock.data[112].x * NnVfx2EmitterDynamicParam.data[0].w;
    temp_120 = floatBitsToInt(sysEmitterStaticUniformBlock.data[137].x);
    if (temp_119)
    {
        temp_120 = temp_118 + 0xFFFFFC00;
    }
    temp_121 = temp_120;
    if (!temp_119)
    {
        temp_121 = (0 - temp_118) + 0x8400;
    }
    temp_122 = clamp(fma(1.0 / fma(fma(temp_116, 0.5, temp_115 * 0.5) * (1.0 / fma(0.0, temp_116, temp_115)), NnVfx2ViewParam.data[30].w, (0.0 - NnVfx2ViewParam.data[30].y)), (0.0 - NnVfx2ViewParam.data[30].z), (0.0 - sysEmitterStaticUniformBlock.data[137].x)) * (1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[137].x) + sysEmitterStaticUniformBlock.data[137].y)), 0.0, 1.0);
    temp_123 = float(temp_121 + 0x77FF);
    out_attr0.x = sysEmitterStaticUniformBlock.data[104].x * NnVfx2EmitterDynamicParam.data[0].x * sysEmitterStaticUniformBlock.data[103].x;
    temp_124 = temp_123 * 3.88322115;
    temp_125 = fma(temp_123 * 2.0, -1.6276572E-05, 0.999983728);
    temp_126 = abs(temp_125) + -0.0;
    temp_127 = fma((0.0 - temp_21) + temp_27.y, temp_97, temp_21);
    out_attr0.y = sysEmitterStaticUniformBlock.data[104].y * NnVfx2EmitterDynamicParam.data[0].y * sysEmitterStaticUniformBlock.data[103].x;
    temp_128 = fma((0.0 - temp_20) + temp_27.x, temp_97, temp_20);
    temp_129 = temp_125 < 0.0 ? 1.0 : 0.0;
    temp_130 = fma(fma(fma(temp_126, -0.0187293, 0.0742610022), temp_126, -0.2121144), temp_126, 1.5707288) * sqrt((0.0 - abs(temp_125)) + 1.0);
    temp_131 = fma(temp_34, sysEmitterStaticUniformBlock.data[142].y, fma(fma((sysEmitterStaticUniformBlock.data[142].y + (0.0 - sysEmitterStaticUniformBlock.data[141].y)) * temp_29, temp_33, sysEmitterStaticUniformBlock.data[141].y), temp_36, fma(fma(temp_31, (sysEmitterStaticUniformBlock.data[141].y + (0.0 - sysEmitterStaticUniformBlock.data[140].y)) * temp_24, sysEmitterStaticUniformBlock.data[140].y), temp_35, fma(temp_30, (0.0 - sysEmitterStaticUniformBlock.data[140].y), sysEmitterStaticUniformBlock.data[140].y)))) * sysScaleAttr.y * NnVfx2EmitterDynamicParam.data[3].z * fma(0.5, sysEmitterStaticUniformBlock.data[15].y, temp_127);
    temp_132 = (clamp(min(0.0, temp_10) + -0.0, 0.0, 1.0) + sysScaleAttr.x) * fma(temp_34, sysEmitterStaticUniformBlock.data[142].x, fma(fma((sysEmitterStaticUniformBlock.data[142].x + (0.0 - sysEmitterStaticUniformBlock.data[141].x)) * temp_29, temp_33, sysEmitterStaticUniformBlock.data[141].x), temp_36, fma(fma(temp_31, (sysEmitterStaticUniformBlock.data[141].x + (0.0 - sysEmitterStaticUniformBlock.data[140].x)) * temp_24, sysEmitterStaticUniformBlock.data[140].x), temp_35, fma(temp_30, (0.0 - sysEmitterStaticUniformBlock.data[140].x), sysEmitterStaticUniformBlock.data[140].x)))) * NnVfx2EmitterDynamicParam.data[3].y * fma(0.5, sysEmitterStaticUniformBlock.data[15].x, temp_128);
    out_attr0.z = sysEmitterStaticUniformBlock.data[104].z * NnVfx2EmitterDynamicParam.data[0].z * sysEmitterStaticUniformBlock.data[103].x;
    temp_133 = fma(temp_34, sysEmitterStaticUniformBlock.data[142].z, fma(fma((sysEmitterStaticUniformBlock.data[142].z + (0.0 - sysEmitterStaticUniformBlock.data[141].z)) * temp_29, temp_33, sysEmitterStaticUniformBlock.data[141].z), temp_36, fma(fma(temp_31, (sysEmitterStaticUniformBlock.data[141].z + (0.0 - sysEmitterStaticUniformBlock.data[140].z)) * temp_24, sysEmitterStaticUniformBlock.data[140].z), temp_35, fma(temp_30, (0.0 - sysEmitterStaticUniformBlock.data[140].z), sysEmitterStaticUniformBlock.data[140].z)))) * sysScaleAttr.z * NnVfx2EmitterDynamicParam.data[3].w * fma(0.5, sysEmitterStaticUniformBlock.data[15].z, temp_108);
    out_attr1.x = temp_122 * NnVfx2EmitterDynamicParam.data[3].x;
    temp_134 = 0.0 + fma(temp_133, temp_96, fma(temp_132, temp_94, sin(temp_86) * (0.0 - temp_131)));
    temp_135 = sin(fma(temp_129, 3.1415927, fma(temp_130 * temp_129, -2.0, temp_130)));
    temp_136 = 0.0 + fma(temp_104, temp_133, fma(temp_98, temp_132, temp_131 * temp_95));
    temp_137 = 0.0 + fma(temp_99, temp_133, fma(temp_103, temp_132, temp_131 * temp_91));
    temp_138 = fma(0.0, temp_133, fma(0.0, temp_132, 0.0 * temp_131)) + 1.0;
    temp_139 = temp_108 == 0.0 && temp_128 == 0.0 && temp_127 == 0.0;
    temp_140 = fma(temp_97, (0.0 - temp_76) + temp_125, temp_76);
    temp_141 = fma(temp_97, fma(cos(temp_124), temp_135, (0.0 - temp_107)), temp_107);
    temp_142 = fma(temp_114, temp_138, fma(temp_137, NnVfx2EmitterDynamicParam.data[8].z, fma(temp_136, NnVfx2EmitterDynamicParam.data[8].y, temp_134 * NnVfx2EmitterDynamicParam.data[8].x)));
    temp_143 = fma(temp_113, temp_138, fma(temp_137, NnVfx2EmitterDynamicParam.data[9].z, fma(temp_136, NnVfx2EmitterDynamicParam.data[9].y, temp_134 * NnVfx2EmitterDynamicParam.data[9].x)));
    out_attr3.x = temp_142;
    temp_144 = fma(temp_97, fma(temp_135, sin(temp_124), (0.0 - temp_105)), temp_105);
    out_attr3.y = temp_143;
    temp_145 = temp_141;
    temp_146 = temp_140;
    temp_147 = temp_144;
    if (!temp_139)
    {
        temp_145 = fma(temp_128, sysEmitterStaticUniformBlock.data[14].y, temp_141);
    }
    temp_148 = temp_145;
    if (!temp_139)
    {
        temp_146 = fma(temp_127, sysEmitterStaticUniformBlock.data[14].y, temp_140);
    }
    temp_149 = temp_146;
    temp_150 = fma(temp_112, temp_138, fma(temp_137, NnVfx2EmitterDynamicParam.data[10].z, fma(temp_136, NnVfx2EmitterDynamicParam.data[10].y, temp_134 * NnVfx2EmitterDynamicParam.data[10].x)));
    out_attr3.z = temp_150;
    if (!temp_139)
    {
        temp_147 = fma(temp_108, sysEmitterStaticUniformBlock.data[14].y, temp_144);
    }
    temp_151 = temp_147;
    temp_152 = fma(temp_150, NnVfx2ViewParam.data[0].z, fma(temp_143, NnVfx2ViewParam.data[0].y, temp_142 * NnVfx2ViewParam.data[0].x)) + NnVfx2ViewParam.data[0].w;
    temp_153 = fma(temp_150, NnVfx2ViewParam.data[1].z, fma(temp_143, NnVfx2ViewParam.data[1].y, temp_142 * NnVfx2ViewParam.data[1].x)) + NnVfx2ViewParam.data[1].w;
    temp_154 = fma(temp_150, NnVfx2ViewParam.data[2].z, fma(temp_143, NnVfx2ViewParam.data[2].y, temp_142 * NnVfx2ViewParam.data[2].x)) + NnVfx2ViewParam.data[2].w;
    temp_155 = inversesqrt(fma(temp_154, temp_154, fma(temp_153, temp_153, temp_152 * temp_152)));
    temp_156 = fma(temp_150, NnVfx2ViewParam.data[3].z, fma(temp_143, NnVfx2ViewParam.data[3].y, temp_142 * NnVfx2ViewParam.data[3].x)) + NnVfx2ViewParam.data[3].w;
    temp_157 = 0.0 + fma(temp_96, temp_151, fma(temp_94, temp_148, sin(temp_86) * (0.0 - temp_149)));
    gl_Position.z = fma(temp_156, NnVfx2ViewParam.data[6].w, fma(temp_154, NnVfx2ViewParam.data[6].z, fma(temp_153, NnVfx2ViewParam.data[6].y, temp_152 * NnVfx2ViewParam.data[6].x)));
    gl_Position.w = fma(temp_156, NnVfx2ViewParam.data[7].w, fma(temp_154, NnVfx2ViewParam.data[7].z, fma(temp_153, NnVfx2ViewParam.data[7].y, temp_152 * NnVfx2ViewParam.data[7].x)));
    gl_Position.x = fma(temp_156, NnVfx2ViewParam.data[4].w, fma(temp_154, NnVfx2ViewParam.data[4].z, fma(temp_153, NnVfx2ViewParam.data[4].y, temp_152 * NnVfx2ViewParam.data[4].x)));
    gl_Position.y = fma(temp_156, NnVfx2ViewParam.data[5].w, fma(temp_154, NnVfx2ViewParam.data[5].z, fma(temp_153, NnVfx2ViewParam.data[5].y, temp_152 * NnVfx2ViewParam.data[5].x)));
    out_attr9.x = temp_152 * temp_155;
    temp_158 = 0.0 + fma(temp_104, temp_151, fma(temp_98, temp_148, temp_95 * temp_149));
    temp_159 = 0.0 + fma(temp_99, temp_151, fma(temp_103, temp_148, temp_91 * temp_149));
    out_attr9.y = temp_153 * temp_155;
    out_attr6.x = sysCustomShaderUniformBlock0.data[36].w;
    out_attr5.x = (0.0 - fma(temp_150, sysCustomShaderUniformBlock0.data[38].z, fma(temp_143, sysCustomShaderUniformBlock0.data[38].y, temp_142 * sysCustomShaderUniformBlock0.data[38].x))) + -0.0;
    out_attr9.z = temp_154 * temp_155;
    out_attr4.z = fma(0.0, temp_112, fma(temp_159, NnVfx2EmitterDynamicParam.data[10].z, fma(temp_158, NnVfx2EmitterDynamicParam.data[10].y, temp_157 * NnVfx2EmitterDynamicParam.data[10].x)));
    out_attr4.y = fma(0.0, temp_113, fma(temp_159, NnVfx2EmitterDynamicParam.data[9].z, fma(temp_158, NnVfx2EmitterDynamicParam.data[9].y, temp_157 * NnVfx2EmitterDynamicParam.data[9].x)));
    if (0.0 < sysCustomShaderUniformBlock1.data[4].w)
    {
        temp_160 = (0.0 - temp_114) + temp_142;
        temp_161 = (0.0 - temp_113) + temp_143;
        temp_162 = (0.0 - temp_112) + temp_150;
        out_attr8.x = fma(fma(temp_162, NnVfx2ViewParam.data[0].z, fma(temp_161, NnVfx2ViewParam.data[0].y, temp_160 * NnVfx2ViewParam.data[0].x)), sysCustomShaderUniformBlock0.data[31].x, 0.5) * sysCustomShaderUniformBlock0.data[41].x;
        out_attr8.y = fma(fma(temp_162, NnVfx2ViewParam.data[1].z, fma(temp_161, NnVfx2ViewParam.data[1].y, temp_160 * NnVfx2ViewParam.data[1].x)), (0.0 - sysCustomShaderUniformBlock0.data[31].y), 0.5) * sysCustomShaderUniformBlock0.data[41].x;
    }
    out_attr4.x = fma(0.0, temp_114, fma(temp_159, NnVfx2EmitterDynamicParam.data[8].z, fma(temp_158, NnVfx2EmitterDynamicParam.data[8].y, temp_157 * NnVfx2EmitterDynamicParam.data[8].x)));
    if (!(temp_122 <= 0.0))
    {
        return;
    }
    gl_Position.x = 0.0;
    gl_Position.y = 0.0;
    gl_Position.z = NnVfx2ViewParam.data[30].y * 5.0;
    out_attr1.x = 0.0;
    return;
}
