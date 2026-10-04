// static_grsn.bfsha model VfxGeneralShader program 1385 (frag)
// sampler sysCustomShaderTextureArraySampler1 -> loc 8 -> material sampler ?
// sampler sysCustomShaderTextureSampler3 -> loc 13 -> material sampler ?
// sampler sysCustomShaderTextureSampler4 -> loc 14 -> material sampler ?
// ubo NnVfx2ViewParam -> loc 5 (labelled)
// ubo sysCustomShaderUniformBlock0 -> loc 11
// ubo sysCustomShaderUniformBlock1 -> loc 12
// ubo sysCustomShaderUniformBlock2 -> loc 13
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

layout (binding = 15, std140) uniform _sysCustomShaderUniformBlock1
{
    precise vec4 data[4096];
} sysCustomShaderUniformBlock1;

layout (binding = 14, std140) uniform _sysCustomShaderUniformBlock0
{
    precise vec4 data[4096];
} sysCustomShaderUniformBlock0;

layout (binding = 8, std140) uniform _NnVfx2ViewParam
{
    precise vec4 data[4096];
} NnVfx2ViewParam;

layout (binding = 1, std140) uniform _fp_c1
{
    precise vec4 data[4096];
} fp_c1;

layout (binding = 0) uniform sampler2D sysCustomShaderTextureSampler3;
layout (binding = 1) uniform sampler2D sysCustomShaderTextureSampler4;
layout (binding = 2) uniform sampler2DArray sysCustomShaderTextureArraySampler1;
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

layout (location = 0) out vec4 sysOutputColor0;


void main()
{
    bool temp_0;
    precise float temp_1;
    precise float temp_2;
    precise float temp_3;
    precise float temp_4;
    precise float temp_5;
    precise float temp_6;
    precise float temp_7;
    precise float temp_8;
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
    bool temp_33;
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
    precise vec3 temp_65;
    precise float temp_66;
    precise float temp_67;
    precise float temp_68;
    precise vec3 temp_69;
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
    uint temp_85;
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
    int temp_96;
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
    int temp_107;
    int temp_108;
    precise float temp_109;
    precise float temp_110;
    precise float temp_111;
    int temp_112;
    bool temp_113;
    int temp_114;
    uint temp_115;
    int temp_116;
    uint temp_117;
    uint temp_118;
    int temp_119;
    uint temp_120;
    precise float temp_121;
    precise float temp_122;
    precise float temp_123;
    bool temp_124;
    precise float temp_125;
    precise float temp_126;
    precise float temp_127;
    uint temp_128;
    int temp_129;
    uint temp_130;
    precise float temp_131;
    precise float temp_132;
    precise float temp_133;
    precise float temp_134;
    uint temp_135;
    int temp_136;
    uint temp_137;
    uint temp_138;
    precise float temp_139;
    int temp_140;
    precise float temp_141;
    int temp_142;
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
    temp_113 = false;
    temp_0 = 0.0 < sysCustomShaderUniformBlock1.data[4].w;
    temp_1 = intBitsToFloat(undef);
    if (temp_0)
    {
        temp_1 = sysCustomShaderUniformBlock0.data[41].z;
    }
    temp_2 = temp_1;
    temp_3 = intBitsToFloat(undef);
    temp_4 = temp_2;
    if (temp_0)
    {
        temp_3 = sysCustomShaderUniformBlock0.data[42].y;
    }
    temp_5 = intBitsToFloat(undef);
    if (temp_0)
    {
        temp_5 = in_attr8.y;
    }
    temp_6 = temp_5;
    temp_7 = intBitsToFloat(undef);
    temp_8 = temp_6;
    if (temp_0)
    {
        temp_7 = in_attr8.x;
    }
    temp_9 = temp_7;
    temp_10 = intBitsToFloat(undef);
    temp_11 = temp_9;
    if (temp_0)
    {
        temp_10 = fma(temp_6, temp_2, sysCustomShaderUniformBlock0.data[42].x);
    }
    temp_12 = temp_10;
    temp_13 = temp_12;
    if (temp_0)
    {
        temp_4 = fma(temp_9, temp_2, sysCustomShaderUniformBlock0.data[42].x);
    }
    temp_14 = temp_4;
    temp_15 = temp_14;
    if (temp_0)
    {
        temp_8 = temp_6 + sysCustomShaderUniformBlock0.data[41].y;
    }
    temp_16 = temp_8;
    temp_17 = temp_16;
    if (temp_0)
    {
        temp_11 = temp_9 + sysCustomShaderUniformBlock0.data[41].y;
    }
    temp_18 = intBitsToFloat(undef);
    if (temp_0)
    {
        temp_18 = temp_12;
    }
    if (temp_0)
    {
        temp_13 = temp_14;
    }
    temp_19 = temp_13;
    temp_20 = temp_19;
    if (temp_0)
    {
        temp_15 = sin(temp_18);
    }
    temp_21 = temp_15;
    temp_22 = temp_21;
    if (temp_0)
    {
        temp_20 = sin(temp_19);
    }
    if (temp_0)
    {
        temp_22 = temp_21 * temp_20;
    }
    temp_23 = temp_22;
    if (temp_0)
    {
        temp_17 = fma(temp_23, sysCustomShaderUniformBlock0.data[41].w, temp_16);
    }
    temp_24 = intBitsToFloat(undef);
    if (temp_0)
    {
        temp_24 = fma(temp_23, sysCustomShaderUniformBlock0.data[41].w, temp_11);
    }
    temp_25 = temp_24;
    temp_26 = intBitsToFloat(undef);
    temp_27 = temp_25;
    if (temp_0)
    {
        temp_26 = fma(temp_3, sysCustomShaderUniformBlock0.data[42].x, temp_17);
    }
    if (temp_0)
    {
        temp_27 = texture(sysCustomShaderTextureSampler3, vec2(temp_25, temp_26)).x;
    }
    temp_28 = in_attr9.z;
    temp_29 = in_attr9.x;
    temp_30 = in_attr4.x;
    temp_31 = in_attr4.y;
    temp_32 = in_attr4.z;
    temp_33 = floatBitsToInt(fma(float((gl_FrontFacing ? -1 : 0)), -2.0, -1.0)) <= 0;
    temp_34 = in_attr9.y;
    temp_35 = inversesqrt(fma(temp_29, temp_29, temp_28 * temp_28));
    temp_36 = temp_30;
    temp_37 = temp_31;
    temp_38 = temp_32;
    if (temp_33)
    {
        temp_36 = (0.0 - temp_30) + -0.0;
    }
    temp_39 = temp_36;
    if (temp_33)
    {
        temp_37 = (0.0 - temp_31) + -0.0;
    }
    temp_40 = temp_37;
    if (temp_33)
    {
        temp_38 = (0.0 - temp_32) + -0.0;
    }
    temp_41 = temp_38;
    temp_42 = temp_28 * (0.0 - temp_35);
    temp_43 = temp_29 * temp_35;
    temp_44 = temp_34 * (0.0 - temp_42);
    temp_45 = inversesqrt(fma(temp_41, temp_41, fma(temp_40, temp_40, temp_39 * temp_39)));
    temp_46 = temp_34 * (0.0 - temp_43);
    temp_47 = fma(temp_28, (0.0 - temp_42), (0.0 - temp_29 * (0.0 - temp_43)));
    temp_48 = temp_45 * temp_39;
    temp_49 = temp_45 * temp_40;
    temp_50 = temp_45 * temp_41;
    temp_51 = inversesqrt(fma(temp_44, temp_44, fma(temp_47, temp_47, temp_46 * temp_46)));
    temp_52 = fma(temp_50, NnVfx2ViewParam.data[0].z, fma(temp_49, NnVfx2ViewParam.data[0].y, temp_48 * NnVfx2ViewParam.data[0].x));
    temp_53 = fma(temp_50, NnVfx2ViewParam.data[1].z, fma(temp_49, NnVfx2ViewParam.data[1].y, temp_48 * NnVfx2ViewParam.data[1].x));
    temp_54 = fma(temp_50, NnVfx2ViewParam.data[2].z, fma(temp_49, NnVfx2ViewParam.data[2].y, temp_48 * NnVfx2ViewParam.data[2].x));
    temp_55 = fma(temp_43, temp_54, temp_42 * temp_52);
    temp_56 = fma(temp_54, temp_44 * (0.0 - temp_51), fma(temp_53, temp_47 * temp_51, temp_52 * temp_46 * temp_51));
    temp_57 = clamp(sysCustomShaderUniformBlock1.data[4].z * 0.699999988, 0.0, 1.0);
    temp_58 = fma(fma(temp_28, (0.0 - temp_54), fma(temp_34, (0.0 - temp_53), temp_29 * (0.0 - temp_52))), fma(temp_28, (0.0 - temp_54), fma(temp_34, (0.0 - temp_53), temp_29 * (0.0 - temp_52))), fma(temp_56, temp_56, temp_55 * temp_55));
    temp_59 = in_attr0.y * fma(fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].y), sysCustomShaderUniformBlock1.data[2].y), temp_57, sysCustomShaderUniformBlock1.data[3].y * sysCustomShaderUniformBlock1.data[3].w);
    temp_60 = temp_58;
    if (temp_0)
    {
        temp_60 = 0.5;
    }
    temp_61 = in_attr0.z * fma(fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].z), sysCustomShaderUniformBlock1.data[2].z), temp_57, sysCustomShaderUniformBlock1.data[3].z * sysCustomShaderUniformBlock1.data[3].w);
    temp_62 = fma(temp_61, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_61);
    temp_63 = fma(temp_59, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_59);
    temp_64 = fma(in_attr0.x * fma(fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].x), sysCustomShaderUniformBlock1.data[2].x), temp_57, sysCustomShaderUniformBlock1.data[3].x * sysCustomShaderUniformBlock1.data[3].w), (0.0 - sysCustomShaderUniformBlock1.data[0].y), in_attr0.x * fma(fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].x), sysCustomShaderUniformBlock1.data[2].x), temp_57, sysCustomShaderUniformBlock1.data[3].x * sysCustomShaderUniformBlock1.data[3].w));
    if (temp_0)
    {
        temp_65 = texture(sysCustomShaderTextureSampler4, vec2(temp_60, temp_27)).xyz;
        temp_62 = temp_65.z;
        temp_63 = temp_65.y;
        temp_64 = temp_65.x;
    }
    temp_66 = temp_62;
    temp_67 = temp_63;
    temp_68 = temp_64;
    temp_69 = texture(sysCustomShaderTextureArraySampler1, vec3(fma(temp_55 * inversesqrt(temp_58), 0.5, 0.5), fma(temp_56 * inversesqrt(temp_58), -0.5, 0.5), float(6))).xyz;
    temp_70 = in_attr7.x;
    temp_71 = in_attr7.z;
    temp_72 = fma(temp_49 + -1.0, 0.7, 1.0);
    temp_73 = temp_48 * 0.699999988;
    temp_74 = inversesqrt(fma(sysCustomShaderUniformBlock0.data[1].z, sysCustomShaderUniformBlock0.data[1].z, fma(sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].x * sysCustomShaderUniformBlock0.data[1].x)));
    temp_75 = temp_50 * 0.699999988;
    temp_76 = inversesqrt(fma(temp_75, temp_75, fma(temp_72, temp_72, temp_73 * temp_73)));
    temp_77 = temp_73 * temp_76;
    temp_78 = temp_72 * temp_76;
    temp_79 = temp_75 * temp_76;
    temp_80 = temp_77 * temp_78;
    temp_81 = clamp(fma(temp_50, temp_74 * sysCustomShaderUniformBlock0.data[1].z, fma(temp_49, temp_74 * sysCustomShaderUniformBlock0.data[1].y, temp_48 * temp_74 * sysCustomShaderUniformBlock0.data[1].x)), 0.0, 1.0);
    temp_82 = temp_78 * temp_79;
    temp_83 = temp_79 * temp_79;
    temp_84 = (0.0 - in_attr3.y) + NnVfx2ViewParam.data[29].y;
    temp_85 = uint(max(0, min(int(trunc((temp_71 + (0.0 - sysCustomShaderUniformBlock2.data[0x226].z)) * sysCustomShaderUniformBlock2.data[0x227].z)), 19)) * 20 + max(0, min(int(trunc((temp_70 + (0.0 - sysCustomShaderUniformBlock2.data[0x226].x)) * sysCustomShaderUniformBlock2.data[0x227].x)), 19)) << 4) >> 2;
    temp_86 = sysCustomShaderUniformBlock2.data[int(temp_85 >> 2)][int(temp_85) & 3];
    temp_87 = (0.0 - in_attr3.x) + NnVfx2ViewParam.data[29].x;
    temp_88 = temp_77 * temp_79;
    temp_89 = fma(temp_77, temp_77, (0.0 - temp_78 * temp_78));
    temp_90 = (0.0 - in_attr3.z) + NnVfx2ViewParam.data[29].z;
    temp_91 = inversesqrt(fma(temp_90, temp_90, fma(temp_84, temp_84, temp_87 * temp_87)));
    temp_92 = temp_81 + fma(temp_81, (0.0 - sysCustomShaderUniformBlock1.data[0].w), sysCustomShaderUniformBlock1.data[0].w);
    temp_93 = temp_87 * temp_91;
    temp_94 = temp_84 * temp_91;
    temp_95 = temp_90 * temp_91;
    temp_96 = floatBitsToInt(temp_86);
    temp_97 = 0.0;
    temp_98 = 0.0;
    temp_99 = 0.0;
    temp_100 = 0.0;
    temp_101 = 0.0;
    temp_102 = 0.0;
    if (floatBitsToInt(temp_86) != -1)
    {
        temp_103 = max(sysCustomShaderUniformBlock1.data[0].x, 0.0001);
        temp_104 = fma(temp_103, 0.5, 0.5);
        temp_105 = temp_104 * 0.5 * temp_104;
        temp_106 = temp_103 * temp_103;
        temp_107 = 0;
        do
        {
            temp_108 = temp_96;
            temp_109 = temp_97;
            temp_110 = temp_98;
            temp_111 = temp_99;
            temp_112 = temp_108 & 255;
            temp_100 = temp_111;
            temp_101 = temp_110;
            temp_102 = temp_109;
            temp_113 = uint(temp_112) >= 30u;
            if (temp_113)
            {
                break;
            }
            temp_114 = temp_112 << 4;
            temp_115 = uint(temp_114 + 0x1CC0) >> 2;
            temp_116 = int(temp_115) + 1;
            temp_117 = uint(temp_114 + 0x1CC8) >> 2;
            temp_118 = uint(temp_114 + 0x1AE0) >> 2;
            temp_119 = int(temp_118) + 1;
            temp_120 = uint(temp_114 + 0x2080) >> 2;
            temp_121 = (0.0 - temp_70) + sysCustomShaderUniformBlock2.data[int(temp_115 >> 2)][int(temp_115) & 3];
            temp_122 = sysCustomShaderUniformBlock2.data[int(uint(temp_116) >> 2)][temp_116 & 3] + (0.0 - in_attr7.y);
            temp_123 = (0.0 - temp_71) + sysCustomShaderUniformBlock2.data[int(temp_117 >> 2)][int(temp_117) & 3];
            temp_124 = floatBitsToInt(sysCustomShaderUniformBlock2.data[int(temp_120 >> 2)][int(temp_120) & 3]) != 0;
            temp_125 = fma(temp_123, temp_123, fma(temp_122, temp_122, temp_121 * temp_121));
            temp_126 = temp_121 * inversesqrt(temp_125);
            temp_127 = temp_122 * inversesqrt(temp_125);
            temp_128 = uint(temp_114 + 0x1900) >> 2;
            temp_129 = int(temp_128) + 1;
            temp_130 = uint(temp_114 + 0x1908) >> 2;
            temp_131 = temp_123 * inversesqrt(temp_125);
            temp_132 = temp_48 * temp_126;
            temp_133 = temp_132;
            if (!temp_124)
            {
                temp_133 = 1.0;
            }
            temp_134 = temp_133;
            if (temp_124)
            {
                temp_135 = uint(temp_114 + 0x1EA0) >> 2;
                temp_136 = int(temp_135) + 1;
                temp_137 = uint(temp_114 + 0x1EA8) >> 2;
                temp_138 = uint(temp_114 + 0x1AE8) >> 2;
                temp_139 = sysCustomShaderUniformBlock2.data[int(temp_138 >> 2)][int(temp_138) & 3];
                temp_140 = int(temp_138) + 1;
                temp_134 = exp2(sysCustomShaderUniformBlock2.data[int(uint(temp_140) >> 2)][temp_140 & 3] * log2(clamp(((0.0 - temp_139) + fma(temp_131, (0.0 - sysCustomShaderUniformBlock2.data[int(temp_137 >> 2)][int(temp_137) & 3]), fma(temp_127, (0.0 - sysCustomShaderUniformBlock2.data[int(uint(temp_136) >> 2)][temp_136 & 3]), temp_126 * (0.0 - sysCustomShaderUniformBlock2.data[int(temp_135 >> 2)][int(temp_135) & 3])))) * (1.0 / ((0.0 - temp_139) + 1.0)), 0.0, 1.0)));
            }
            temp_141 = temp_93 + temp_126;
            temp_142 = temp_107 + 1;
            temp_143 = temp_94 + temp_127;
            temp_144 = temp_95 + temp_131;
            temp_145 = max(fma(temp_50, temp_131, fma(temp_49, temp_127, temp_48 * temp_126)), 1E-08);
            temp_146 = inversesqrt(fma(temp_144, temp_144, fma(temp_143, temp_143, temp_141 * temp_141)));
            temp_147 = temp_141 * temp_146;
            temp_148 = temp_143 * temp_146;
            temp_149 = temp_144 * temp_146;
            temp_150 = max(fma(temp_95, temp_149, fma(temp_94, temp_148, temp_93 * temp_147)), 1E-08);
            temp_151 = max(fma(temp_50, temp_149, fma(temp_49, temp_148, temp_48 * temp_147)), 1E-08) * max(fma(temp_50, temp_149, fma(temp_49, temp_148, temp_48 * temp_147)), 1E-08);
            temp_152 = clamp(fma(temp_50, temp_131, fma(temp_49, temp_127, temp_132)), 0.0, 1.0) * exp2(sysCustomShaderUniformBlock2.data[int(uint(temp_119) >> 2)][temp_119 & 3] * log2(clamp(fma(sysCustomShaderUniformBlock2.data[int(temp_118 >> 2)][int(temp_118) & 3], (0.0 - sqrt(temp_125)), 1.0), 0.0, 1.0))) * temp_134;
            temp_153 = sysCustomShaderUniformBlock2.data[int(temp_130 >> 2)][int(temp_130) & 3] * temp_152;
            temp_154 = sysCustomShaderUniformBlock2.data[int(temp_128 >> 2)][int(temp_128) & 3] * temp_152;
            temp_155 = sysCustomShaderUniformBlock2.data[int(uint(temp_129) >> 2)][temp_129 & 3] * temp_152;
            temp_156 = (fma(exp2(temp_150 * fma(temp_150, -5.55473, -6.98316002)), (0.0 - sysCustomShaderUniformBlock1.data[0].z), exp2(temp_150 * fma(temp_150, -5.55473, -6.98316002))) + sysCustomShaderUniformBlock1.data[0].z) * 1.0 / (temp_105 + fma(max(fma(temp_50, temp_95, fma(temp_49, temp_94, temp_48 * temp_93)), 1E-08), (0.0 - temp_105), max(fma(temp_50, temp_95, fma(temp_49, temp_94, temp_48 * temp_93)), 1E-08))) * (1.0 / (temp_105 + fma(temp_105, (0.0 - temp_145), temp_145))) * temp_106 * (1.0 / max(fma(temp_151, temp_106 * temp_106, (0.0 - temp_151)) + 1.0, 1E-08)) * temp_106 * (1.0 / max(fma(temp_151, temp_106 * temp_106, (0.0 - temp_151)) + 1.0, 1E-08));
            temp_157 = fma(temp_154 * temp_156, 0.07957747, fma(temp_154, temp_68 * 0.318309873, temp_110));
            temp_158 = fma(temp_155 * temp_156, 0.07957747, fma(temp_155, temp_67 * 0.318309873, temp_111));
            temp_159 = fma(temp_153 * temp_156, 0.07957747, fma(temp_153, temp_66 * 0.318309873, temp_109));
            temp_96 = int(uint(temp_108) >> 8);
            temp_107 = temp_142;
            temp_97 = temp_159;
            temp_98 = temp_157;
            temp_99 = temp_158;
            temp_100 = temp_158;
            temp_101 = temp_157;
            temp_102 = temp_159;
        }
        while (!(temp_142 >= 4));
    }
    temp_113 = false;
    temp_160 = fma(temp_59, sysCustomShaderUniformBlock1.data[2].w, fma(temp_69.y, sysCustomShaderUniformBlock1.data[0].z, fma(temp_92 * sysCustomShaderUniformBlock0.data[0].y * temp_67, 0.31830987, max(0.0, fma(temp_89, sysCustomShaderUniformBlock0.data[29].y, fma(temp_79, sysCustomShaderUniformBlock0.data[24].z, fma(temp_78, sysCustomShaderUniformBlock0.data[24].y, temp_77 * sysCustomShaderUniformBlock0.data[24].x)) + sysCustomShaderUniformBlock0.data[24].w + fma(temp_88, sysCustomShaderUniformBlock0.data[27].w, fma(temp_83, sysCustomShaderUniformBlock0.data[27].z, fma(temp_82, sysCustomShaderUniformBlock0.data[27].y, temp_80 * sysCustomShaderUniformBlock0.data[27].x))))) * fma(temp_67, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_67))) + temp_100);
    temp_161 = fma(temp_61, sysCustomShaderUniformBlock1.data[2].w, fma(temp_69.z, sysCustomShaderUniformBlock1.data[0].z, fma(temp_92 * sysCustomShaderUniformBlock0.data[0].z * temp_66, 0.31830987, max(0.0, fma(temp_89, sysCustomShaderUniformBlock0.data[29].z, fma(temp_79, sysCustomShaderUniformBlock0.data[25].z, fma(temp_78, sysCustomShaderUniformBlock0.data[25].y, temp_77 * sysCustomShaderUniformBlock0.data[25].x)) + sysCustomShaderUniformBlock0.data[25].w + fma(temp_88, sysCustomShaderUniformBlock0.data[28].w, fma(temp_83, sysCustomShaderUniformBlock0.data[28].z, fma(temp_82, sysCustomShaderUniformBlock0.data[28].y, temp_80 * sysCustomShaderUniformBlock0.data[28].x))))) * fma(temp_66, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_66))) + temp_102);
    temp_162 = inversesqrt(fma(sysCustomShaderUniformBlock0.data[1].z, sysCustomShaderUniformBlock0.data[1].z, fma(sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].x * sysCustomShaderUniformBlock0.data[1].x)));
    temp_163 = in_attr3.x + (0.0 - NnVfx2ViewParam.data[29].x);
    temp_164 = in_attr3.y + (0.0 - NnVfx2ViewParam.data[29].y);
    temp_165 = in_attr3.z + (0.0 - NnVfx2ViewParam.data[29].z);
    temp_166 = fma(temp_165, temp_165, fma(temp_164, temp_164, temp_163 * temp_163));
    temp_167 = clamp(fma(in_attr5.x, sysCustomShaderUniformBlock0.data[37].y, sysCustomShaderUniformBlock0.data[37].x), 0.0, 1.0) * in_attr6.x;
    temp_168 = exp2(max(fma(fma(temp_162 * sysCustomShaderUniformBlock0.data[1].z, (0.0 - temp_165 * inversesqrt(temp_166)), fma(temp_162 * sysCustomShaderUniformBlock0.data[1].y, (0.0 - temp_164 * inversesqrt(temp_166)), temp_162 * sysCustomShaderUniformBlock0.data[1].x * (0.0 - temp_163 * inversesqrt(temp_166)))), (0.0 - sysCustomShaderUniformBlock0.data[35].y), sysCustomShaderUniformBlock0.data[35].y), 1E-08)) * exp2(log2(clamp(1.0 / NnVfx2ViewParam.data[30].w * sqrt(temp_166), 0.0, 1.0)) * sysCustomShaderUniformBlock0.data[35].x);
    temp_169 = fma((0.0 - temp_160) + sysCustomShaderUniformBlock0.data[36].y, temp_167, temp_160);
    temp_170 = fma(in_attr0.x * fma(fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].x), sysCustomShaderUniformBlock1.data[2].x), clamp(sysCustomShaderUniformBlock1.data[4].z * 0.699999988, 0.0, 1.0), sysCustomShaderUniformBlock1.data[3].x * sysCustomShaderUniformBlock1.data[3].w), sysCustomShaderUniformBlock1.data[2].w, fma(temp_69.x, sysCustomShaderUniformBlock1.data[0].z, fma(temp_92 * sysCustomShaderUniformBlock0.data[0].x * temp_68, 0.31830987, max(0.0, fma(temp_89, sysCustomShaderUniformBlock0.data[29].x, fma(temp_79, sysCustomShaderUniformBlock0.data[23].z, fma(temp_78, sysCustomShaderUniformBlock0.data[23].y, temp_77 * sysCustomShaderUniformBlock0.data[23].x)) + sysCustomShaderUniformBlock0.data[23].w + fma(temp_88, sysCustomShaderUniformBlock0.data[26].w, fma(temp_83, sysCustomShaderUniformBlock0.data[26].z, fma(temp_82, sysCustomShaderUniformBlock0.data[26].y, temp_80 * sysCustomShaderUniformBlock0.data[26].x))))) * fma(temp_68, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_68))) + temp_101);
    temp_171 = fma((0.0 - temp_161) + sysCustomShaderUniformBlock0.data[36].z, temp_167, temp_161);
    temp_172 = fma((0.0 - temp_170) + sysCustomShaderUniformBlock0.data[36].x, temp_167, temp_170);
    temp_173 = clamp((0.0 - exp2(clamp(fma(sqrt(temp_166), sysCustomShaderUniformBlock0.data[33].y, sysCustomShaderUniformBlock0.data[33].x), 0.0, 1.0) * (0.0 - sysCustomShaderUniformBlock0.data[33].z) * 1.44269502)) + 1.0, 0.0, 1.0) * sysCustomShaderUniformBlock0.data[32].w;
    sysOutputColor0.x = fma((0.0 - temp_172) + fma(fma(temp_168 * sysCustomShaderUniformBlock0.data[34].x, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].x)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].x), temp_173, temp_172);
    sysOutputColor0.y = fma((0.0 - temp_169) + fma(fma(temp_168 * sysCustomShaderUniformBlock0.data[34].y, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].y)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].y), temp_173, temp_169);
    sysOutputColor0.z = fma((0.0 - temp_171) + fma(fma(temp_168 * sysCustomShaderUniformBlock0.data[34].z, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].z)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].z), temp_173, temp_171);
    sysOutputColor0.w = clamp(fma(clamp(in_attr0.w * in_attr2.w, 0.0, 1.0) * in_attr1.x, sysCustomShaderUniformBlock1.data[11].x, sysCustomShaderUniformBlock1.data[11].y), 0.0, 1.0);
    return;
}
