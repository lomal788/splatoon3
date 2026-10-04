// static_grsn.bfsha model VfxGeneralShader program 1383 (vert)
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
    int temp_24;
    precise float temp_25;
    precise vec4 temp_26;
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
    int temp_41;
    bool temp_42;
    int temp_43;
    precise float temp_44;
    precise float temp_45;
    precise float temp_46;
    precise float temp_47;
    int temp_48;
    int temp_49;
    int temp_50;
    int temp_51;
    int temp_52;
    bool temp_53;
    precise float temp_54;
    precise float temp_55;
    int temp_56;
    bool temp_57;
    int temp_58;
    int temp_59;
    bool temp_60;
    int temp_61;
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
    bool temp_75;
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
    int temp_93;
    precise float temp_94;
    int temp_95;
    int temp_96;
    precise float temp_97;
    int temp_98;
    precise float temp_99;
    precise float temp_100;
    int temp_101;
    precise float temp_102;
    precise float temp_103;
    precise float temp_104;
    precise float temp_105;
    bool temp_106;
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
    int temp_117;
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
    bool temp_130;
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
    temp_24 = temp_18;
    temp_25 = temp_23;
    if (temp_18 < int(trunc(temp_15 + -1.0)))
    {
        temp_24 = temp_18 + 1;
    }
    temp_26 = texelFetch(sysTextureSampler2, ivec2(TexelFetchScale(temp_24, 0), TexelFetchScale(temp_14, 0)), 0).xyzw;
    temp_27 = temp_26.w;
    temp_28 = 1.0 / ((0.0 - sysEmitterStaticUniformBlock.data[140].w) + sysEmitterStaticUniformBlock.data[141].w);
    temp_29 = 1.0 / (sysEmitterStaticUniformBlock.data[142].w + (0.0 - sysEmitterStaticUniformBlock.data[141].w));
    temp_30 = temp_13 + (0.0 - sysEmitterStaticUniformBlock.data[141].w);
    temp_31 = temp_13 + (0.0 - sysEmitterStaticUniformBlock.data[140].w);
    temp_32 = temp_13 >= sysEmitterStaticUniformBlock.data[140].w ? 1.0 : 0.0;
    temp_33 = fma((sysEmitterStaticUniformBlock.data[142].z + (0.0 - sysEmitterStaticUniformBlock.data[141].z)) * temp_29, temp_30, sysEmitterStaticUniformBlock.data[141].z);
    temp_34 = temp_13 >= sysEmitterStaticUniformBlock.data[141].w ? 1.0 : 0.0;
    temp_35 = temp_13 >= sysEmitterStaticUniformBlock.data[142].w ? 1.0 : 0.0;
    temp_36 = fma(temp_32, (0.0 - temp_34), temp_32);
    temp_37 = fma(temp_34, (0.0 - temp_35), temp_34);
    temp_38 = floor(temp_10 * 2.0);
    temp_39 = sysRandomAttr.z;
    temp_40 = sysRandomAttr.y;
    temp_41 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x20000000;
    temp_42 = temp_23 < 0.0;
    temp_43 = 0;
    temp_44 = intBitsToFloat(temp_41);
    temp_45 = sysEmitterStaticUniformBlock.data[162].w;
    temp_46 = temp_33;
    if (temp_42)
    {
        temp_25 = (0.0 - temp_23) + -0.0;
    }
    temp_47 = temp_25;
    if (temp_42)
    {
        temp_43 = 0x8000;
    }
    temp_48 = temp_43;
    temp_49 = int(trunc(log2(temp_47)));
    temp_50 = temp_49;
    temp_51 = temp_48;
    if (log2(temp_47) < 0.0)
    {
        temp_50 = temp_49 + -1;
    }
    temp_52 = temp_50;
    temp_53 = sysEmitterStaticUniformBlock.data[162].w == 1.0;
    temp_54 = floor(temp_39 * 2.0);
    temp_55 = sysInitRotateAttr.x;
    temp_56 = (temp_52 + 15 << 10) + int(trunc(fma(exp2(float((0 - temp_52))) * temp_47, 1024.0, -1024.0))) + temp_48;
    temp_57 = temp_56 < 0x8000;
    if (temp_57)
    {
        temp_51 = temp_56 + 0xFFFFFC00;
    }
    temp_58 = temp_51;
    if (!temp_57)
    {
        temp_58 = (0 - temp_56) + 0x8400;
    }
    temp_59 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x10000000;
    temp_60 = 0.0 == sysEmitterStaticUniformBlock.data[162].w;
    temp_61 = floatBitsToInt(sysEmitterStaticUniformBlock.data[7].x) & 0x40000000;
    temp_62 = float(temp_58 + 0x77FF);
    if (!temp_60)
    {
        temp_44 = log2(abs(sysEmitterStaticUniformBlock.data[162].w));
    }
    temp_63 = temp_44;
    if (temp_60)
    {
        temp_63 = 1.0;
    }
    temp_64 = temp_63;
    temp_65 = temp_62 * 3.88322115;
    temp_66 = temp_64;
    if (!temp_53)
    {
        temp_45 = (0.0 - sysEmitterStaticUniformBlock.data[162].w) + 1.0;
    }
    temp_67 = temp_45;
    temp_68 = fma(temp_62 * 2.0, -1.6276572E-05, 0.999983728);
    temp_69 = temp_67;
    if (!temp_53)
    {
        temp_69 = 1.0 / temp_67;
    }
    if (!temp_60)
    {
        temp_46 = temp_3 * temp_64;
    }
    temp_70 = ((0.0 - temp_54 < 0.0 ? 1.0 : 0.0) + (temp_54 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_59 > 0 ? -1 : 0)) + (0 - temp_59 >= 0 ? 0 : 1)));
    temp_71 = sysInitRotateAttr.y;
    temp_72 = abs(temp_68) + -0.0;
    temp_73 = intBitsToFloat(undef);
    if (!temp_60)
    {
        temp_73 = temp_46;
    }
    if (!temp_60)
    {
        temp_66 = exp2(temp_73);
    }
    temp_74 = temp_68 < 0.0 ? 1.0 : 0.0;
    temp_75 = temp_27 < 0.0;
    if (!temp_53)
    {
        temp_7 = fma(temp_69, (0.0 - temp_66), temp_69);
    }
    temp_76 = temp_7;
    temp_77 = ((0.0 - temp_38 < 0.0 ? 1.0 : 0.0) + (temp_38 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_41 > 0 ? -1 : 0)) + (0 - temp_41 >= 0 ? 0 : 1)));
    temp_78 = fma(fma(fma(temp_72, -0.0187293, 0.0742610022), temp_72, -0.2121144), temp_72, 1.5707288) * sqrt((0.0 - abs(temp_68)) + 1.0);
    temp_79 = fma(fma(temp_10 + temp_40, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].x, 2.0, sysEmitterStaticUniformBlock.data[162].x);
    temp_80 = sin(fma(temp_74, 3.1415927, fma(temp_78 * temp_74, -2.0, temp_78)));
    temp_81 = fma(fma(temp_40 + temp_39, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].y, 2.0, sysEmitterStaticUniformBlock.data[162].y);
    temp_82 = fma(fma(temp_10 + temp_39, 0.5, -0.5) * sysEmitterStaticUniformBlock.data[163].z, 2.0, sysEmitterStaticUniformBlock.data[162].z);
    temp_83 = temp_17 + (0.0 - floor(temp_17));
    temp_84 = fma(fma(temp_79 * temp_70, -2.0, temp_79), temp_76, fma(temp_10 + -0.5, sysEmitterStaticUniformBlock.data[161].x, fma(temp_70 * temp_55, -2.0, temp_55)));
    temp_85 = fma((0.0 - temp_21) + temp_26.y, temp_83, temp_21);
    temp_86 = fma((0.0 - temp_22) + temp_26.z, temp_83, temp_22);
    temp_87 = temp_80 * cos(temp_65);
    temp_88 = temp_80 * sin(temp_65);
    temp_89 = temp_27;
    if (temp_75)
    {
        temp_89 = (0.0 - temp_27) + -0.0;
    }
    temp_90 = temp_89;
    temp_91 = floor(temp_40 * 2.0);
    temp_92 = fma(fma(temp_81 * temp_77, -2.0, temp_81), temp_76, fma(temp_40 + -0.5, sysEmitterStaticUniformBlock.data[161].y, fma(temp_77 * temp_71, -2.0, temp_71)));
    temp_93 = int(trunc(log2(temp_90)));
    temp_94 = sysInitRotateAttr.z;
    temp_95 = temp_93;
    if (log2(temp_90) < 0.0)
    {
        temp_95 = temp_93 + -1;
    }
    temp_96 = temp_95;
    temp_97 = ((0.0 - temp_91 < 0.0 ? 1.0 : 0.0) + (temp_91 > 0.0 ? 1.0 : 0.0)) * float(abs((0 - (temp_61 > 0 ? -1 : 0)) + (0 - temp_61 >= 0 ? 0 : 1)));
    temp_98 = 0;
    if (temp_75)
    {
        temp_98 = 0x8000;
    }
    temp_99 = fma(fma(temp_82 * temp_97, -2.0, temp_82), temp_76, fma(temp_39 + -0.5, sysEmitterStaticUniformBlock.data[161].z, fma(temp_97 * temp_94, -2.0, temp_94)));
    temp_100 = sin(temp_84) * sin(temp_92);
    temp_101 = (temp_96 + 15 << 10) + int(trunc(fma(exp2(float((0 - temp_96))) * temp_90, 1024.0, -1024.0))) + temp_98;
    temp_102 = sin(temp_84) * cos(temp_92);
    temp_103 = sysLocalPosAttr.x;
    temp_104 = sin(temp_92) * cos(temp_84);
    temp_105 = cos(temp_92) * cos(temp_84);
    temp_106 = temp_101 < 0x8000;
    temp_107 = cos(temp_99) * cos(temp_84);
    temp_108 = sin(temp_84) * cos(temp_99);
    temp_109 = cos(temp_92) * cos(temp_99);
    temp_110 = sin(temp_92) * cos(temp_99);
    temp_111 = fma(sin(temp_99), temp_102, (0.0 - temp_104));
    temp_112 = fma(sin(temp_99), temp_104, (0.0 - temp_102));
    temp_113 = fma(sin(temp_99), temp_105, temp_100);
    temp_114 = fma(sin(temp_99), temp_100, temp_105);
    temp_115 = sysLocalPosAttr.z;
    temp_116 = floatBitsToInt(temp_99);
    if (temp_106)
    {
        temp_116 = temp_101 + 0xFFFFFC00;
    }
    temp_117 = temp_116;
    if (!temp_106)
    {
        temp_117 = (0 - temp_101) + 0x8400;
    }
    temp_118 = sysLocalPosAttr.y;
    temp_119 = float(temp_117 + 0x77FF);
    temp_120 = temp_119 * 3.88322115;
    temp_121 = fma(temp_119 * 2.0, -1.6276572E-05, 0.999983728);
    temp_122 = fma((0.0 - temp_20) + temp_26.x, temp_83, temp_20);
    temp_123 = abs(temp_121) + -0.0;
    temp_124 = fma(temp_35, sysEmitterStaticUniformBlock.data[142].y, fma(fma((sysEmitterStaticUniformBlock.data[142].y + (0.0 - sysEmitterStaticUniformBlock.data[141].y)) * temp_29, temp_30, sysEmitterStaticUniformBlock.data[141].y), temp_37, fma(fma(temp_31, (sysEmitterStaticUniformBlock.data[141].y + (0.0 - sysEmitterStaticUniformBlock.data[140].y)) * temp_28, sysEmitterStaticUniformBlock.data[140].y), temp_36, fma(temp_32, (0.0 - sysEmitterStaticUniformBlock.data[140].y), sysEmitterStaticUniformBlock.data[140].y)))) * sysScaleAttr.y * NnVfx2EmitterDynamicParam.data[3].z * fma(0.5, sysEmitterStaticUniformBlock.data[15].y, temp_85);
    temp_125 = fma(temp_115, NnVfx2EmitterDynamicParam.data[5].z, fma(temp_118, NnVfx2EmitterDynamicParam.data[5].y, temp_103 * NnVfx2EmitterDynamicParam.data[5].x)) + NnVfx2EmitterDynamicParam.data[5].w;
    temp_126 = fma(temp_115, NnVfx2EmitterDynamicParam.data[6].z, fma(temp_118, NnVfx2EmitterDynamicParam.data[6].y, temp_103 * NnVfx2EmitterDynamicParam.data[6].x)) + NnVfx2EmitterDynamicParam.data[6].w;
    out_attr7.y = temp_125;
    out_attr7.z = temp_126;
    temp_127 = (clamp(min(0.0, temp_10) + -0.0, 0.0, 1.0) + sysScaleAttr.x) * fma(temp_35, sysEmitterStaticUniformBlock.data[142].x, fma(fma((sysEmitterStaticUniformBlock.data[142].x + (0.0 - sysEmitterStaticUniformBlock.data[141].x)) * temp_29, temp_30, sysEmitterStaticUniformBlock.data[141].x), temp_37, fma(fma(temp_31, (sysEmitterStaticUniformBlock.data[141].x + (0.0 - sysEmitterStaticUniformBlock.data[140].x)) * temp_28, sysEmitterStaticUniformBlock.data[140].x), temp_36, fma(temp_32, (0.0 - sysEmitterStaticUniformBlock.data[140].x), sysEmitterStaticUniformBlock.data[140].x)))) * NnVfx2EmitterDynamicParam.data[3].y * fma(0.5, sysEmitterStaticUniformBlock.data[15].x, temp_122);
    temp_128 = temp_121 < 0.0 ? 1.0 : 0.0;
    temp_129 = fma(temp_115, NnVfx2EmitterDynamicParam.data[4].z, fma(temp_118, NnVfx2EmitterDynamicParam.data[4].y, temp_103 * NnVfx2EmitterDynamicParam.data[4].x)) + NnVfx2EmitterDynamicParam.data[4].w;
    temp_130 = temp_86 == 0.0 && temp_122 == 0.0 && temp_85 == 0.0;
    out_attr7.x = temp_129;
    temp_131 = fma(fma(fma(temp_123, -0.0187293, 0.0742610022), temp_123, -0.2121144), temp_123, 1.5707288) * sqrt((0.0 - abs(temp_121)) + 1.0);
    temp_132 = fma(temp_35, sysEmitterStaticUniformBlock.data[142].z, fma(temp_33, temp_37, fma(fma(temp_31, (sysEmitterStaticUniformBlock.data[141].z + (0.0 - sysEmitterStaticUniformBlock.data[140].z)) * temp_28, sysEmitterStaticUniformBlock.data[140].z), temp_36, fma(temp_32, (0.0 - sysEmitterStaticUniformBlock.data[140].z), sysEmitterStaticUniformBlock.data[140].z)))) * sysScaleAttr.z * NnVfx2EmitterDynamicParam.data[3].w * fma(0.5, sysEmitterStaticUniformBlock.data[15].z, temp_86);
    temp_133 = 0.0 + fma(temp_132, temp_110, fma(temp_127, temp_109, sin(temp_99) * (0.0 - temp_124)));
    out_attr0.w = sysEmitterStaticUniformBlock.data[112].x * NnVfx2EmitterDynamicParam.data[0].w;
    temp_134 = 0.0 + fma(temp_112, temp_132, fma(temp_113, temp_127, temp_124 * temp_107));
    temp_135 = 0.0 + fma(temp_114, temp_132, fma(temp_111, temp_127, temp_124 * temp_108));
    temp_136 = sin(fma(temp_128, 3.1415927, fma(temp_131 * temp_128, -2.0, temp_131)));
    temp_137 = fma(0.0, temp_132, fma(0.0, temp_127, 0.0 * temp_124)) + 1.0;
    temp_138 = fma(temp_83, (0.0 - temp_68) + temp_121, temp_68);
    temp_139 = temp_138;
    if (!temp_130)
    {
        temp_139 = fma(temp_85, sysEmitterStaticUniformBlock.data[14].y, temp_138);
    }
    temp_140 = temp_139;
    temp_141 = fma(temp_129, temp_137, fma(temp_135, NnVfx2EmitterDynamicParam.data[8].z, fma(temp_134, NnVfx2EmitterDynamicParam.data[8].y, temp_133 * NnVfx2EmitterDynamicParam.data[8].x)));
    out_attr3.x = temp_141;
    temp_142 = fma(temp_83, fma(cos(temp_120), temp_136, (0.0 - temp_87)), temp_87);
    temp_143 = fma(temp_126, temp_137, fma(temp_135, NnVfx2EmitterDynamicParam.data[10].z, fma(temp_134, NnVfx2EmitterDynamicParam.data[10].y, temp_133 * NnVfx2EmitterDynamicParam.data[10].x)));
    temp_144 = fma(temp_125, temp_137, fma(temp_135, NnVfx2EmitterDynamicParam.data[9].z, fma(temp_134, NnVfx2EmitterDynamicParam.data[9].y, temp_133 * NnVfx2EmitterDynamicParam.data[9].x)));
    out_attr3.z = temp_143;
    temp_145 = fma(temp_83, fma(temp_136, sin(temp_120), (0.0 - temp_88)), temp_88);
    out_attr3.y = temp_144;
    temp_146 = temp_142;
    temp_147 = temp_145;
    if (!temp_130)
    {
        temp_146 = fma(temp_122, sysEmitterStaticUniformBlock.data[14].y, temp_142);
    }
    temp_148 = temp_146;
    if (!temp_130)
    {
        temp_147 = fma(temp_86, sysEmitterStaticUniformBlock.data[14].y, temp_145);
    }
    temp_149 = temp_147;
    out_attr0.y = sysEmitterStaticUniformBlock.data[104].y * NnVfx2EmitterDynamicParam.data[0].y * sysEmitterStaticUniformBlock.data[103].x;
    out_attr0.x = sysEmitterStaticUniformBlock.data[104].x * NnVfx2EmitterDynamicParam.data[0].x * sysEmitterStaticUniformBlock.data[103].x;
    out_attr0.z = sysEmitterStaticUniformBlock.data[104].z * NnVfx2EmitterDynamicParam.data[0].z * sysEmitterStaticUniformBlock.data[103].x;
    temp_150 = fma(temp_143, NnVfx2ViewParam.data[0].z, fma(temp_144, NnVfx2ViewParam.data[0].y, temp_141 * NnVfx2ViewParam.data[0].x)) + NnVfx2ViewParam.data[0].w;
    temp_151 = fma(temp_143, NnVfx2ViewParam.data[1].z, fma(temp_144, NnVfx2ViewParam.data[1].y, temp_141 * NnVfx2ViewParam.data[1].x)) + NnVfx2ViewParam.data[1].w;
    temp_152 = fma(temp_143, NnVfx2ViewParam.data[2].z, fma(temp_144, NnVfx2ViewParam.data[2].y, temp_141 * NnVfx2ViewParam.data[2].x)) + NnVfx2ViewParam.data[2].w;
    temp_153 = fma(temp_143, NnVfx2ViewParam.data[3].z, fma(temp_144, NnVfx2ViewParam.data[3].y, temp_141 * NnVfx2ViewParam.data[3].x)) + NnVfx2ViewParam.data[3].w;
    temp_154 = inversesqrt(fma(temp_152, temp_152, fma(temp_151, temp_151, temp_150 * temp_150)));
    out_attr5.x = (0.0 - fma(temp_143, sysCustomShaderUniformBlock0.data[38].z, fma(temp_144, sysCustomShaderUniformBlock0.data[38].y, temp_141 * sysCustomShaderUniformBlock0.data[38].x))) + -0.0;
    temp_155 = 0.0 + fma(temp_110, temp_149, fma(temp_109, temp_148, sin(temp_99) * (0.0 - temp_140)));
    temp_156 = 0.0 + fma(temp_112, temp_149, fma(temp_113, temp_148, temp_107 * temp_140));
    gl_Position.w = fma(temp_153, NnVfx2ViewParam.data[7].w, fma(temp_152, NnVfx2ViewParam.data[7].z, fma(temp_151, NnVfx2ViewParam.data[7].y, temp_150 * NnVfx2ViewParam.data[7].x)));
    gl_Position.y = fma(temp_153, NnVfx2ViewParam.data[5].w, fma(temp_152, NnVfx2ViewParam.data[5].z, fma(temp_151, NnVfx2ViewParam.data[5].y, temp_150 * NnVfx2ViewParam.data[5].x)));
    gl_Position.z = fma(temp_153, NnVfx2ViewParam.data[6].w, fma(temp_152, NnVfx2ViewParam.data[6].z, fma(temp_151, NnVfx2ViewParam.data[6].y, temp_150 * NnVfx2ViewParam.data[6].x)));
    gl_Position.x = fma(temp_153, NnVfx2ViewParam.data[4].w, fma(temp_152, NnVfx2ViewParam.data[4].z, fma(temp_151, NnVfx2ViewParam.data[4].y, temp_150 * NnVfx2ViewParam.data[4].x)));
    out_attr9.x = temp_150 * temp_154;
    temp_157 = 0.0 + fma(temp_114, temp_149, fma(temp_111, temp_148, temp_108 * temp_140));
    out_attr1.x = NnVfx2EmitterDynamicParam.data[3].x;
    out_attr6.x = sysCustomShaderUniformBlock0.data[36].w;
    out_attr9.y = temp_151 * temp_154;
    out_attr9.z = temp_152 * temp_154;
    out_attr4.z = fma(0.0, temp_126, fma(temp_157, NnVfx2EmitterDynamicParam.data[10].z, fma(temp_156, NnVfx2EmitterDynamicParam.data[10].y, temp_155 * NnVfx2EmitterDynamicParam.data[10].x)));
    out_attr4.y = fma(0.0, temp_125, fma(temp_157, NnVfx2EmitterDynamicParam.data[9].z, fma(temp_156, NnVfx2EmitterDynamicParam.data[9].y, temp_155 * NnVfx2EmitterDynamicParam.data[9].x)));
    if (0.0 < sysCustomShaderUniformBlock1.data[4].w)
    {
        temp_158 = (0.0 - temp_129) + temp_141;
        temp_159 = (0.0 - temp_125) + temp_144;
        temp_160 = (0.0 - temp_126) + temp_143;
        out_attr8.x = fma(fma(temp_160, NnVfx2ViewParam.data[0].z, fma(temp_159, NnVfx2ViewParam.data[0].y, temp_158 * NnVfx2ViewParam.data[0].x)), sysCustomShaderUniformBlock0.data[31].x, 0.5) * sysCustomShaderUniformBlock0.data[41].x;
        out_attr8.y = fma(fma(temp_160, NnVfx2ViewParam.data[1].z, fma(temp_159, NnVfx2ViewParam.data[1].y, temp_158 * NnVfx2ViewParam.data[1].x)), (0.0 - sysCustomShaderUniformBlock0.data[31].y), 0.5) * sysCustomShaderUniformBlock0.data[41].x;
    }
    out_attr4.x = fma(0.0, temp_129, fma(temp_157, NnVfx2EmitterDynamicParam.data[8].z, fma(temp_156, NnVfx2EmitterDynamicParam.data[8].y, temp_155 * NnVfx2EmitterDynamicParam.data[8].x)));
    return;
}
