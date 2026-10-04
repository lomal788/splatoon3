// static_grsn.bfsha model VfxGeneralShader program 1202 (frag)
// sampler sysCustomShaderTextureArraySampler1 -> loc 8 -> material sampler ?
// sampler sysCustomShaderTextureSampler3 -> loc 13 -> material sampler ?
// sampler sysCustomShaderTextureSampler4 -> loc 14 -> material sampler ?
// sampler sysTextureSampler1 -> loc 1 -> material sampler ?
// sampler sysTextureSampler2 -> loc 2 -> material sampler ?
// ubo NnVfx2ViewParam -> loc 5 (labelled)
// ubo sysCustomShaderUniformBlock0 -> loc 11
// ubo sysCustomShaderUniformBlock1 -> loc 12
// ubo sysCustomShaderUniformBlock2 -> loc 13
// ubo sysEmitterStaticUniformBlock -> loc 6 (labelled)
// out sysOutputColor0 -> loc 0
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

layout (binding = 16, std140) uniform _sysCustomShaderUniformBlock2
{
    precise vec4 data[4096];
} sysCustomShaderUniformBlock2;

layout (binding = 9, std140) uniform _sysEmitterStaticUniformBlock
{
    precise vec4 data[4096];
} sysEmitterStaticUniformBlock;

layout (binding = 15, std140) uniform _sysCustomShaderUniformBlock1
{
    precise vec4 data[4096];
} sysCustomShaderUniformBlock1;

layout (binding = 8, std140) uniform _NnVfx2ViewParam
{
    precise vec4 data[4096];
} NnVfx2ViewParam;

layout (binding = 14, std140) uniform _sysCustomShaderUniformBlock0
{
    precise vec4 data[4096];
} sysCustomShaderUniformBlock0;

layout (binding = 1, std140) uniform _fp_c1
{
    precise vec4 data[4096];
} fp_c1;

layout (binding = 0) uniform sampler2D sysTextureSampler2;
layout (binding = 1) uniform sampler2D sysTextureSampler1;
layout (binding = 2) uniform sampler2D sysCustomShaderTextureSampler3;
layout (binding = 3) uniform sampler2D sysCustomShaderTextureSampler4;
layout (binding = 4) uniform sampler2DArray sysCustomShaderTextureArraySampler1;
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
layout (location = 11) in vec4 in_attr11;
layout (location = 12) in vec4 in_attr12;
layout (location = 13) in vec4 in_attr13;

layout (location = 0) out vec4 sysOutputColor0;


void main()
{
    precise float temp_0;
    precise float temp_1;
    precise float temp_2;
    precise float temp_3;
    precise float temp_4;
    precise float temp_5;
    precise float temp_6;
    precise float temp_7;
    bool temp_8;
    int temp_9;
    int temp_10;
    int temp_11;
    int temp_12;
    precise vec2 temp_13;
    precise float temp_14;
    precise float temp_15;
    precise float temp_16;
    precise float temp_17;
    precise float temp_18;
    precise float temp_19;
    precise float temp_20;
    bool temp_21;
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
    bool temp_34;
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
    precise vec3 temp_98;
    precise float temp_99;
    precise float temp_100;
    precise float temp_101;
    precise vec3 temp_102;
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
    uint temp_117;
    precise float temp_118;
    precise float temp_119;
    precise float temp_120;
    precise float temp_121;
    precise float temp_122;
    precise float temp_123;
    int temp_124;
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
    int temp_135;
    int temp_136;
    precise float temp_137;
    precise float temp_138;
    precise float temp_139;
    int temp_140;
    bool temp_141;
    int temp_142;
    uint temp_143;
    int temp_144;
    uint temp_145;
    uint temp_146;
    int temp_147;
    precise float temp_148;
    precise float temp_149;
    precise float temp_150;
    precise float temp_151;
    uint temp_152;
    precise float temp_153;
    precise float temp_154;
    precise float temp_155;
    uint temp_156;
    precise float temp_157;
    uint temp_158;
    int temp_159;
    bool temp_160;
    precise float temp_161;
    precise float temp_162;
    uint temp_163;
    int temp_164;
    uint temp_165;
    uint temp_166;
    precise float temp_167;
    int temp_168;
    precise float temp_169;
    int temp_170;
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
    precise float temp_200;
    precise float temp_201;
    precise float temp_202;
    precise float temp_203;
    precise float temp_204;
    precise float temp_205;
    precise float temp_206;
    temp_141 = false;
    temp_0 = in_attr2.y;
    temp_1 = in_attr1.z;
    temp_2 = in_attr1.w;
    temp_3 = texture(sysTextureSampler2, vec2(in_attr2.x, temp_0)).w;
    temp_4 = in_attr4.w;
    temp_5 = temp_3 * texture(sysTextureSampler1, vec2(temp_1, temp_2)).w;
    temp_6 = temp_5 * temp_4;
    temp_7 = clamp(temp_6 * in_attr0.w, 0.0, 1.0) * in_attr3.x;
    temp_8 = temp_7 <= sysEmitterStaticUniformBlock.data[138].z;
    temp_9 = floatBitsToInt(temp_3);
    temp_10 = floatBitsToInt(temp_0);
    temp_11 = floatBitsToInt(temp_5);
    temp_12 = floatBitsToInt(temp_4);
    if (temp_8)
    {
        discard;
    }
    temp_13 = texture(sysTextureSampler1, vec2(temp_1, temp_2)).xy;
    if (temp_8)
    {
        temp_9 = 0;
    }
    if (temp_8)
    {
        temp_10 = 0;
    }
    if (temp_8)
    {
        temp_11 = 0;
    }
    if (temp_8)
    {
        temp_12 = 0;
    }
    if (temp_8)
    {
        sysOutputColor0.x = intBitsToFloat(temp_9);
        sysOutputColor0.y = intBitsToFloat(temp_10);
        sysOutputColor0.z = intBitsToFloat(temp_11);
        sysOutputColor0.w = intBitsToFloat(temp_12);
        return;
    }
    temp_14 = temp_13.x * sysCustomShaderUniformBlock1.data[6].x;
    temp_15 = temp_13.y * sysCustomShaderUniformBlock1.data[6].x;
    temp_16 = in_attr6.x;
    temp_17 = in_attr6.y;
    temp_18 = in_attr6.z;
    temp_19 = sqrt((0.0 - clamp(fma(temp_15, temp_15, temp_14 * temp_14), 0.0, 1.0)) + 1.0);
    temp_20 = temp_15 * in_attr8.x;
    temp_21 = floatBitsToInt(fma(float((gl_FrontFacing ? -1 : 0)), -2.0, -1.0)) <= 0;
    temp_22 = (0.0 - in_attr5.x) + NnVfx2ViewParam.data[29].x;
    temp_23 = temp_15 * in_attr8.z;
    temp_24 = (0.0 - in_attr5.y) + NnVfx2ViewParam.data[29].y;
    temp_25 = (0.0 - in_attr5.z) + NnVfx2ViewParam.data[29].z;
    temp_26 = fma(temp_14, in_attr7.z, temp_23);
    temp_27 = temp_16;
    temp_28 = temp_17;
    temp_29 = temp_23;
    temp_30 = temp_26;
    temp_31 = temp_14;
    temp_32 = temp_20;
    if (temp_21)
    {
        temp_27 = (0.0 - temp_16) + -0.0;
    }
    if (temp_21)
    {
        temp_28 = (0.0 - temp_17) + -0.0;
    }
    temp_33 = temp_18;
    if (temp_21)
    {
        temp_33 = (0.0 - temp_18) + -0.0;
    }
    temp_34 = 0.0 < sysCustomShaderUniformBlock1.data[4].w;
    temp_35 = fma(temp_19, temp_27, fma(temp_14, in_attr7.x, temp_20));
    temp_36 = fma(temp_19, temp_28, fma(temp_14, in_attr7.y, temp_15 * in_attr8.y));
    temp_37 = fma(temp_19, temp_33, temp_26);
    if (temp_34)
    {
        temp_29 = in_attr12.y;
    }
    temp_38 = temp_29;
    if (temp_34)
    {
        temp_30 = in_attr12.x;
    }
    temp_39 = temp_30;
    temp_40 = temp_39;
    if (temp_34)
    {
        temp_31 = sysCustomShaderUniformBlock0.data[41].z;
    }
    temp_41 = temp_31;
    temp_42 = inversesqrt(fma(temp_25, temp_25, fma(temp_24, temp_24, temp_22 * temp_22)));
    temp_43 = inversesqrt(fma(temp_37, temp_37, fma(temp_36, temp_36, temp_35 * temp_35)));
    temp_44 = temp_22 * temp_42;
    temp_45 = temp_24 * temp_42;
    temp_46 = temp_25 * temp_42;
    temp_47 = temp_35 * temp_43;
    temp_48 = temp_36 * temp_43;
    temp_49 = temp_37 * temp_43;
    temp_50 = temp_42;
    temp_51 = temp_41;
    if (temp_34)
    {
        temp_50 = fma(temp_38, temp_41, sysCustomShaderUniformBlock0.data[42].x);
    }
    if (temp_34)
    {
        temp_51 = fma(temp_39, temp_41, sysCustomShaderUniformBlock0.data[42].x);
    }
    temp_52 = temp_51;
    temp_53 = sysEmitterStaticUniformBlock.data[138].z + sysCustomShaderUniformBlock1.data[4].y;
    temp_54 = temp_52;
    temp_55 = fma(temp_48, temp_45, temp_47 * temp_44);
    if (temp_34)
    {
        temp_32 = temp_52;
    }
    if (temp_34)
    {
        temp_54 = sin(temp_32);
    }
    temp_56 = temp_54;
    temp_57 = temp_6 + (0.0 - temp_53);
    temp_58 = log2(clamp(fma(temp_49, temp_46, temp_55), 0.0, 1.0)) * sysCustomShaderUniformBlock1.data[4].x;
    temp_59 = temp_57;
    temp_60 = temp_58;
    temp_61 = temp_56;
    if (temp_34)
    {
        temp_59 = sysCustomShaderUniformBlock0.data[42].y;
    }
    temp_62 = temp_59;
    temp_63 = temp_62;
    if (temp_34)
    {
        temp_60 = sin(temp_50);
    }
    temp_64 = temp_60;
    temp_65 = temp_64;
    temp_66 = exp2(temp_58);
    if (temp_34)
    {
        temp_65 = temp_64 * temp_56;
    }
    temp_67 = temp_65;
    temp_68 = exp2(temp_58) * temp_57 * (1.0 / ((0.0 - temp_53) + 1.0));
    if (temp_34)
    {
        temp_66 = fma(temp_68, sysCustomShaderUniformBlock0.data[41].y, temp_38);
    }
    temp_69 = temp_66;
    temp_70 = temp_69;
    if (temp_34)
    {
        temp_40 = fma(temp_68, sysCustomShaderUniformBlock0.data[41].y, temp_39);
    }
    if (temp_34)
    {
        temp_70 = fma(temp_67, sysCustomShaderUniformBlock0.data[41].w, temp_69);
    }
    if (temp_34)
    {
        temp_61 = fma(temp_67, sysCustomShaderUniformBlock0.data[41].w, temp_40);
    }
    temp_71 = temp_61;
    temp_72 = temp_71;
    if (temp_34)
    {
        temp_63 = fma(temp_62, sysCustomShaderUniformBlock0.data[42].x, temp_70);
    }
    if (temp_34)
    {
        temp_72 = texture(sysCustomShaderTextureSampler3, vec2(temp_71, temp_63)).x;
    }
    temp_73 = in_attr13.z;
    temp_74 = in_attr13.x;
    temp_75 = in_attr13.y;
    temp_76 = fma(temp_49, NnVfx2ViewParam.data[1].z, fma(temp_48, NnVfx2ViewParam.data[1].y, temp_47 * NnVfx2ViewParam.data[1].x));
    temp_77 = clamp(clamp(min(temp_68, 0.7) + -0.0, 0.0, 1.0) * sysCustomShaderUniformBlock1.data[4].z, 0.0, 1.0);
    temp_78 = inversesqrt(fma(temp_74, temp_74, temp_73 * temp_73));
    temp_79 = temp_74 * temp_78;
    temp_80 = temp_73 * (0.0 - temp_78);
    temp_81 = temp_75 * (0.0 - temp_79);
    temp_82 = temp_75 * (0.0 - temp_80);
    temp_83 = fma(temp_73, (0.0 - temp_80), (0.0 - temp_74 * (0.0 - temp_79)));
    temp_84 = inversesqrt(fma(temp_82, temp_82, fma(temp_83, temp_83, temp_81 * temp_81)));
    temp_85 = fma(temp_49, NnVfx2ViewParam.data[0].z, fma(temp_48, NnVfx2ViewParam.data[0].y, temp_47 * NnVfx2ViewParam.data[0].x));
    temp_86 = fma(temp_49, NnVfx2ViewParam.data[2].z, fma(temp_48, NnVfx2ViewParam.data[2].y, temp_47 * NnVfx2ViewParam.data[2].x));
    temp_87 = fma(temp_79, temp_86, temp_80 * temp_85);
    temp_88 = fma(temp_86, temp_82 * (0.0 - temp_84), fma(temp_76, temp_83 * temp_84, temp_85 * temp_81 * temp_84));
    temp_89 = inversesqrt(fma(fma(temp_73, (0.0 - temp_86), fma(temp_75, (0.0 - temp_76), temp_74 * (0.0 - temp_85))), fma(temp_73, (0.0 - temp_86), fma(temp_75, (0.0 - temp_76), temp_74 * (0.0 - temp_85))), fma(temp_88, temp_88, temp_87 * temp_87)));
    temp_90 = in_attr4.x * in_attr0.x;
    temp_91 = temp_90 * fma(temp_77, fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].x), sysCustomShaderUniformBlock1.data[2].x), sysCustomShaderUniformBlock1.data[3].x * sysCustomShaderUniformBlock1.data[3].w);
    temp_92 = temp_90;
    if (temp_34)
    {
        temp_92 = 0.5;
    }
    temp_93 = in_attr4.z * in_attr0.z * fma(temp_77, fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].z), sysCustomShaderUniformBlock1.data[2].z), sysCustomShaderUniformBlock1.data[3].z * sysCustomShaderUniformBlock1.data[3].w);
    temp_94 = in_attr4.y * in_attr0.y * fma(temp_77, fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].y), sysCustomShaderUniformBlock1.data[2].y), sysCustomShaderUniformBlock1.data[3].y * sysCustomShaderUniformBlock1.data[3].w);
    temp_95 = fma(temp_91, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_91);
    temp_96 = fma(temp_94, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_94);
    temp_97 = fma(temp_93, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_93);
    if (temp_34)
    {
        temp_98 = texture(sysCustomShaderTextureSampler4, vec2(temp_92, temp_72)).xyz;
        temp_95 = temp_98.x;
        temp_96 = temp_98.y;
        temp_97 = temp_98.z;
    }
    temp_99 = temp_95;
    temp_100 = temp_96;
    temp_101 = temp_97;
    temp_102 = texture(sysCustomShaderTextureArraySampler1, vec3(fma(temp_87 * temp_89, 0.5, 0.5), fma(temp_88 * temp_89, -0.5, 0.5), float(6))).xyz;
    temp_103 = in_attr11.x;
    temp_104 = in_attr11.z;
    temp_105 = temp_47 * 0.699999988;
    temp_106 = fma(temp_48 + -1.0, 0.7, 1.0);
    temp_107 = inversesqrt(fma(sysCustomShaderUniformBlock0.data[1].z, sysCustomShaderUniformBlock0.data[1].z, fma(sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].x * sysCustomShaderUniformBlock0.data[1].x)));
    temp_108 = temp_49 * 0.699999988;
    temp_109 = inversesqrt(fma(temp_108, temp_108, fma(temp_106, temp_106, temp_105 * temp_105)));
    temp_110 = temp_105 * temp_109;
    temp_111 = temp_106 * temp_109;
    temp_112 = temp_108 * temp_109;
    temp_113 = temp_110 * temp_111;
    temp_114 = clamp(fma(temp_49, temp_107 * sysCustomShaderUniformBlock0.data[1].z, fma(temp_48, temp_107 * sysCustomShaderUniformBlock0.data[1].y, temp_47 * temp_107 * sysCustomShaderUniformBlock0.data[1].x)), 0.0, 1.0);
    temp_115 = temp_111 * temp_112;
    temp_116 = temp_112 * temp_112;
    temp_117 = uint(max(0, min(int(trunc((temp_104 + (0.0 - sysCustomShaderUniformBlock2.data[0x226].z)) * sysCustomShaderUniformBlock2.data[0x227].z)), 19)) * 20 + max(0, min(int(trunc((temp_103 + (0.0 - sysCustomShaderUniformBlock2.data[0x226].x)) * sysCustomShaderUniformBlock2.data[0x227].x)), 19)) << 4) >> 2;
    temp_118 = sysCustomShaderUniformBlock2.data[int(temp_117 >> 2)][int(temp_117) & 3];
    temp_119 = temp_110 * temp_112;
    temp_120 = fma(temp_110, temp_110, (0.0 - temp_111 * temp_111));
    temp_121 = temp_114 + fma(temp_114, (0.0 - sysCustomShaderUniformBlock1.data[0].w), sysCustomShaderUniformBlock1.data[0].w);
    temp_122 = clamp(1.0 + (0.0 - sysCustomShaderUniformBlock1.data[1].x), 0.0, 1.0);
    temp_123 = fma(temp_7, sysCustomShaderUniformBlock1.data[11].x, sysCustomShaderUniformBlock1.data[11].y);
    temp_124 = floatBitsToInt(temp_118);
    temp_125 = 0.0;
    temp_126 = 0.0;
    temp_127 = 0.0;
    temp_128 = 0.0;
    temp_129 = 0.0;
    temp_130 = 0.0;
    if (floatBitsToInt(temp_118) != -1)
    {
        temp_131 = max(sysCustomShaderUniformBlock1.data[0].x, 0.0001);
        temp_132 = fma(temp_131, 0.5, 0.5);
        temp_133 = temp_132 * 0.5 * temp_132;
        temp_134 = temp_131 * temp_131;
        temp_135 = 0;
        do
        {
            temp_136 = temp_124;
            temp_137 = temp_125;
            temp_138 = temp_126;
            temp_139 = temp_127;
            temp_140 = temp_136 & 255;
            temp_128 = temp_137;
            temp_129 = temp_138;
            temp_130 = temp_139;
            temp_141 = uint(temp_140) >= 30u;
            if (temp_141)
            {
                break;
            }
            temp_142 = temp_140 << 4;
            temp_143 = uint(temp_142 + 0x1CC0) >> 2;
            temp_144 = int(temp_143) + 1;
            temp_145 = uint(temp_142 + 0x1CC8) >> 2;
            temp_146 = uint(temp_142 + 0x1AE0) >> 2;
            temp_147 = int(temp_146) + 1;
            temp_148 = (0.0 - temp_103) + sysCustomShaderUniformBlock2.data[int(temp_143 >> 2)][int(temp_143) & 3];
            temp_149 = sysCustomShaderUniformBlock2.data[int(uint(temp_144) >> 2)][temp_144 & 3] + (0.0 - in_attr11.y);
            temp_150 = (0.0 - temp_104) + sysCustomShaderUniformBlock2.data[int(temp_145 >> 2)][int(temp_145) & 3];
            temp_151 = fma(temp_150, temp_150, fma(temp_149, temp_149, temp_148 * temp_148));
            temp_152 = uint(temp_142 + 0x2080) >> 2;
            temp_153 = temp_149 * inversesqrt(temp_151);
            temp_154 = temp_150 * inversesqrt(temp_151);
            temp_155 = temp_148 * inversesqrt(temp_151);
            temp_156 = uint(temp_142 + 0x1908) >> 2;
            temp_157 = sysCustomShaderUniformBlock2.data[int(uint(temp_147) >> 2)][temp_147 & 3] * log2(clamp(fma(sysCustomShaderUniformBlock2.data[int(temp_146 >> 2)][int(temp_146) & 3], (0.0 - sqrt(temp_151)), 1.0), 0.0, 1.0));
            temp_158 = uint(temp_142 + 0x1900) >> 2;
            temp_159 = int(temp_158) + 1;
            temp_160 = floatBitsToInt(sysCustomShaderUniformBlock2.data[int(temp_152 >> 2)][int(temp_152) & 3]) != 0;
            temp_161 = temp_157;
            if (!temp_160)
            {
                temp_161 = 1.0;
            }
            temp_162 = temp_161;
            if (temp_160)
            {
                temp_163 = uint(temp_142 + 0x1EA0) >> 2;
                temp_164 = int(temp_163) + 1;
                temp_165 = uint(temp_142 + 0x1EA8) >> 2;
                temp_166 = uint(temp_142 + 0x1AE8) >> 2;
                temp_167 = sysCustomShaderUniformBlock2.data[int(temp_166 >> 2)][int(temp_166) & 3];
                temp_168 = int(temp_166) + 1;
                temp_162 = exp2(sysCustomShaderUniformBlock2.data[int(uint(temp_168) >> 2)][temp_168 & 3] * log2(clamp(((0.0 - temp_167) + fma(temp_154, (0.0 - sysCustomShaderUniformBlock2.data[int(temp_165 >> 2)][int(temp_165) & 3]), fma(temp_153, (0.0 - sysCustomShaderUniformBlock2.data[int(uint(temp_164) >> 2)][temp_164 & 3]), temp_155 * (0.0 - sysCustomShaderUniformBlock2.data[int(temp_163 >> 2)][int(temp_163) & 3])))) * (1.0 / ((0.0 - temp_167) + 1.0)), 0.0, 1.0)));
            }
            temp_169 = temp_44 + temp_155;
            temp_170 = temp_135 + 1;
            temp_171 = temp_45 + temp_153;
            temp_172 = clamp(fma(temp_49, temp_154, fma(temp_48, temp_153, temp_47 * temp_155)), 0.0, 1.0) * exp2(temp_157) * temp_162;
            temp_173 = temp_46 + temp_154;
            temp_174 = sysCustomShaderUniformBlock2.data[int(temp_158 >> 2)][int(temp_158) & 3] * temp_172;
            temp_175 = sysCustomShaderUniformBlock2.data[int(uint(temp_159) >> 2)][temp_159 & 3] * temp_172;
            temp_176 = sysCustomShaderUniformBlock2.data[int(temp_156 >> 2)][int(temp_156) & 3] * temp_172;
            temp_177 = max(fma(temp_49, temp_154, fma(temp_48, temp_153, temp_47 * temp_155)), 1E-08);
            temp_178 = inversesqrt(fma(temp_173, temp_173, fma(temp_171, temp_171, temp_169 * temp_169)));
            temp_179 = temp_169 * temp_178;
            temp_180 = temp_171 * temp_178;
            temp_181 = temp_173 * temp_178;
            temp_182 = max(fma(temp_46, temp_181, fma(temp_45, temp_180, temp_44 * temp_179)), 1E-08);
            temp_183 = max(fma(temp_49, temp_181, fma(temp_48, temp_180, temp_47 * temp_179)), 1E-08) * max(fma(temp_49, temp_181, fma(temp_48, temp_180, temp_47 * temp_179)), 1E-08);
            temp_184 = (fma(exp2(temp_182 * fma(temp_182, -5.55473, -6.98316002)), (0.0 - sysCustomShaderUniformBlock1.data[0].z), exp2(temp_182 * fma(temp_182, -5.55473, -6.98316002))) + sysCustomShaderUniformBlock1.data[0].z) * 1.0 / (temp_133 + fma(max(fma(temp_49, temp_46, temp_55), 1E-08), (0.0 - temp_133), max(fma(temp_49, temp_46, temp_55), 1E-08))) * (1.0 / (temp_133 + fma(temp_133, (0.0 - temp_177), temp_177))) * temp_134 * (1.0 / max(fma(temp_183, temp_134 * temp_134, (0.0 - temp_183)) + 1.0, 1E-08)) * temp_134 * (1.0 / max(fma(temp_183, temp_134 * temp_134, (0.0 - temp_183)) + 1.0, 1E-08));
            temp_185 = fma(temp_174 * temp_184, 0.07957747, fma(temp_174, temp_99 * 0.318309873, temp_137));
            temp_186 = fma(temp_175 * temp_184, 0.07957747, fma(temp_175, temp_100 * 0.318309873, temp_138));
            temp_187 = fma(temp_176 * temp_184, 0.07957747, fma(temp_176, temp_101 * 0.318309873, temp_139));
            temp_124 = int(uint(temp_136) >> 8);
            temp_135 = temp_170;
            temp_125 = temp_185;
            temp_126 = temp_186;
            temp_127 = temp_187;
            temp_128 = temp_185;
            temp_129 = temp_186;
            temp_130 = temp_187;
        }
        while (!(temp_170 >= 4));
    }
    temp_141 = false;
    temp_188 = inversesqrt(fma(sysCustomShaderUniformBlock0.data[1].z, sysCustomShaderUniformBlock0.data[1].z, fma(sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].x * sysCustomShaderUniformBlock0.data[1].x)));
    temp_189 = in_attr5.x + (0.0 - NnVfx2ViewParam.data[29].x);
    temp_190 = in_attr5.y + (0.0 - NnVfx2ViewParam.data[29].y);
    temp_191 = in_attr5.z + (0.0 - NnVfx2ViewParam.data[29].z);
    temp_192 = temp_188 * sysCustomShaderUniformBlock0.data[1].x;
    temp_193 = temp_188 * sysCustomShaderUniformBlock0.data[1].y;
    temp_194 = temp_188 * sysCustomShaderUniformBlock0.data[1].z;
    temp_195 = fma(temp_191, temp_191, fma(temp_190, temp_190, temp_189 * temp_189));
    temp_196 = (sysCustomShaderUniformBlock1.data[1].y + -1.0) * (sysCustomShaderUniformBlock1.data[1].y + -1.0);
    temp_197 = clamp(fma(in_attr9.x, sysCustomShaderUniformBlock0.data[37].y, sysCustomShaderUniformBlock0.data[37].x), 0.0, 1.0) * in_attr10.x;
    temp_198 = clamp(fma(temp_123, (0.0 - sysCustomShaderUniformBlock1.data[1].z), 1.0), 0.0, 1.0) * (fma(temp_196, -0.2, exp2(1.0 / sysCustomShaderUniformBlock1.data[1].y * log2(clamp(max(fma(temp_46, (0.0 - temp_194), fma(temp_45, (0.0 - temp_193), temp_44 * (0.0 - temp_192))), 0.001) + -0.0, 0.0, 1.0))) * temp_196) + 0.200000003);
    temp_199 = exp2(max(fma(fma(temp_194, (0.0 - temp_191 * inversesqrt(temp_195)), fma(temp_193, (0.0 - temp_190 * inversesqrt(temp_195)), temp_192 * (0.0 - temp_189 * inversesqrt(temp_195)))), (0.0 - sysCustomShaderUniformBlock0.data[35].y), sysCustomShaderUniformBlock0.data[35].y), 1E-08)) * exp2(log2(clamp(1.0 / NnVfx2ViewParam.data[30].w * sqrt(temp_195), 0.0, 1.0)) * sysCustomShaderUniformBlock0.data[35].x);
    temp_200 = fma(temp_91, sysCustomShaderUniformBlock1.data[2].w, fma(temp_198 * sqrt(temp_91) * sysCustomShaderUniformBlock0.data[0].w, sysCustomShaderUniformBlock1.data[1].x, fma(temp_102.x, sysCustomShaderUniformBlock1.data[0].z, fma(temp_121 * sysCustomShaderUniformBlock0.data[0].x * temp_99 * temp_122, 0.31830987, max(0.0, fma(temp_120, sysCustomShaderUniformBlock0.data[29].x, fma(temp_112, sysCustomShaderUniformBlock0.data[23].z, fma(temp_111, sysCustomShaderUniformBlock0.data[23].y, temp_110 * sysCustomShaderUniformBlock0.data[23].x)) + sysCustomShaderUniformBlock0.data[23].w + fma(temp_119, sysCustomShaderUniformBlock0.data[26].w, fma(temp_116, sysCustomShaderUniformBlock0.data[26].z, fma(temp_115, sysCustomShaderUniformBlock0.data[26].y, temp_113 * sysCustomShaderUniformBlock0.data[26].x))))) * fma(temp_99, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_99))) + temp_128));
    temp_201 = fma(temp_94, sysCustomShaderUniformBlock1.data[2].w, fma(temp_198 * sqrt(temp_94) * sysCustomShaderUniformBlock0.data[0].w, sysCustomShaderUniformBlock1.data[1].x, fma(temp_102.y, sysCustomShaderUniformBlock1.data[0].z, fma(temp_121 * sysCustomShaderUniformBlock0.data[0].y * temp_100 * temp_122, 0.31830987, max(0.0, fma(temp_120, sysCustomShaderUniformBlock0.data[29].y, fma(temp_112, sysCustomShaderUniformBlock0.data[24].z, fma(temp_111, sysCustomShaderUniformBlock0.data[24].y, temp_110 * sysCustomShaderUniformBlock0.data[24].x)) + sysCustomShaderUniformBlock0.data[24].w + fma(temp_119, sysCustomShaderUniformBlock0.data[27].w, fma(temp_116, sysCustomShaderUniformBlock0.data[27].z, fma(temp_115, sysCustomShaderUniformBlock0.data[27].y, temp_113 * sysCustomShaderUniformBlock0.data[27].x))))) * fma(temp_100, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_100))) + temp_129));
    temp_202 = fma(temp_93, sysCustomShaderUniformBlock1.data[2].w, fma(temp_198 * sqrt(temp_93) * sysCustomShaderUniformBlock0.data[0].w, sysCustomShaderUniformBlock1.data[1].x, fma(temp_102.z, sysCustomShaderUniformBlock1.data[0].z, fma(temp_121 * sysCustomShaderUniformBlock0.data[0].z * temp_101 * temp_122, 0.31830987, max(0.0, fma(temp_120, sysCustomShaderUniformBlock0.data[29].z, fma(temp_112, sysCustomShaderUniformBlock0.data[25].z, fma(temp_111, sysCustomShaderUniformBlock0.data[25].y, temp_110 * sysCustomShaderUniformBlock0.data[25].x)) + sysCustomShaderUniformBlock0.data[25].w + fma(temp_119, sysCustomShaderUniformBlock0.data[28].w, fma(temp_116, sysCustomShaderUniformBlock0.data[28].z, fma(temp_115, sysCustomShaderUniformBlock0.data[28].y, temp_113 * sysCustomShaderUniformBlock0.data[28].x))))) * fma(temp_101, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_101))) + temp_130));
    temp_203 = fma((0.0 - temp_201) + sysCustomShaderUniformBlock0.data[36].y, temp_197, temp_201);
    temp_204 = fma((0.0 - temp_200) + sysCustomShaderUniformBlock0.data[36].x, temp_197, temp_200);
    temp_205 = fma((0.0 - temp_202) + sysCustomShaderUniformBlock0.data[36].z, temp_197, temp_202);
    temp_206 = clamp((0.0 - exp2(clamp(fma(sqrt(temp_195), sysCustomShaderUniformBlock0.data[33].y, sysCustomShaderUniformBlock0.data[33].x), 0.0, 1.0) * (0.0 - sysCustomShaderUniformBlock0.data[33].z) * 1.44269502)) + 1.0, 0.0, 1.0) * sysCustomShaderUniformBlock0.data[32].w;
    sysOutputColor0.x = fma((0.0 - temp_204) + fma(fma(temp_199 * sysCustomShaderUniformBlock0.data[34].x, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].x)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].x), temp_206, temp_204);
    sysOutputColor0.y = fma((0.0 - temp_203) + fma(fma(temp_199 * sysCustomShaderUniformBlock0.data[34].y, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].y)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].y), temp_206, temp_203);
    sysOutputColor0.z = fma((0.0 - temp_205) + fma(fma(temp_199 * sysCustomShaderUniformBlock0.data[34].z, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].z)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].z), temp_206, temp_205);
    sysOutputColor0.w = clamp(temp_123 + -0.0, 0.0, 1.0);
    return;
}
