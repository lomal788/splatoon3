// static_grsn.bfsha model VfxGeneralShader program 1383 (frag)
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

layout (binding = 8, std140) uniform _NnVfx2ViewParam
{
    precise vec4 data[4096];
} NnVfx2ViewParam;

layout (binding = 15, std140) uniform _sysCustomShaderUniformBlock1
{
    precise vec4 data[4096];
} sysCustomShaderUniformBlock1;

layout (binding = 14, std140) uniform _sysCustomShaderUniformBlock0
{
    precise vec4 data[4096];
} sysCustomShaderUniformBlock0;

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
    precise float temp_0;
    precise float temp_1;
    precise float temp_2;
    bool temp_3;
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
    bool temp_14;
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
    precise vec3 temp_76;
    precise float temp_77;
    precise float temp_78;
    precise float temp_79;
    precise vec3 temp_80;
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
    uint temp_94;
    precise float temp_95;
    precise float temp_96;
    precise float temp_97;
    precise float temp_98;
    precise float temp_99;
    int temp_100;
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
    int temp_111;
    int temp_112;
    precise float temp_113;
    precise float temp_114;
    precise float temp_115;
    int temp_116;
    bool temp_117;
    int temp_118;
    uint temp_119;
    int temp_120;
    uint temp_121;
    uint temp_122;
    int temp_123;
    precise float temp_124;
    precise float temp_125;
    precise float temp_126;
    precise float temp_127;
    uint temp_128;
    precise float temp_129;
    uint temp_130;
    precise float temp_131;
    precise float temp_132;
    uint temp_133;
    int temp_134;
    bool temp_135;
    precise float temp_136;
    precise float temp_137;
    uint temp_138;
    int temp_139;
    uint temp_140;
    uint temp_141;
    precise float temp_142;
    int temp_143;
    precise float temp_144;
    precise float temp_145;
    int temp_146;
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
    temp_117 = false;
    temp_0 = in_attr4.x;
    temp_1 = in_attr4.y;
    temp_2 = in_attr4.z;
    temp_3 = floatBitsToInt(fma(float((gl_FrontFacing ? -1 : 0)), -2.0, -1.0)) <= 0;
    temp_4 = temp_0;
    temp_5 = temp_1;
    temp_6 = temp_2;
    if (temp_3)
    {
        temp_4 = (0.0 - temp_0) + -0.0;
    }
    temp_7 = temp_4;
    temp_8 = (0.0 - in_attr3.x) + NnVfx2ViewParam.data[29].x;
    temp_9 = temp_8;
    if (temp_3)
    {
        temp_5 = (0.0 - temp_1) + -0.0;
    }
    temp_10 = temp_5;
    temp_11 = (0.0 - in_attr3.y) + NnVfx2ViewParam.data[29].y;
    temp_12 = temp_11;
    if (temp_3)
    {
        temp_6 = (0.0 - temp_2) + -0.0;
    }
    temp_13 = temp_6;
    temp_14 = 0.0 < sysCustomShaderUniformBlock1.data[4].w;
    temp_15 = (0.0 - in_attr3.z) + NnVfx2ViewParam.data[29].z;
    temp_16 = intBitsToFloat(undef);
    temp_17 = temp_15;
    if (temp_14)
    {
        temp_16 = in_attr8.y;
    }
    temp_18 = temp_16;
    temp_19 = intBitsToFloat(undef);
    temp_20 = temp_18;
    if (temp_14)
    {
        temp_19 = sysCustomShaderUniformBlock0.data[42].y;
    }
    temp_21 = fma(temp_15, temp_15, fma(temp_11, temp_11, temp_8 * temp_8));
    temp_22 = inversesqrt(fma(temp_13, temp_13, fma(temp_10, temp_10, temp_7 * temp_7)));
    temp_23 = temp_8 * inversesqrt(temp_21);
    temp_24 = temp_21;
    if (temp_14)
    {
        temp_9 = in_attr8.x;
    }
    temp_25 = temp_9;
    temp_26 = temp_11 * inversesqrt(temp_21);
    temp_27 = temp_22 * temp_7;
    temp_28 = temp_22 * temp_10;
    temp_29 = temp_15 * inversesqrt(temp_21);
    temp_30 = temp_22 * temp_13;
    temp_31 = temp_25;
    if (temp_14)
    {
        temp_12 = sysCustomShaderUniformBlock0.data[41].z;
    }
    temp_32 = temp_12;
    temp_33 = temp_32;
    if (temp_14)
    {
        temp_17 = fma(temp_18, temp_32, sysCustomShaderUniformBlock0.data[42].x);
    }
    temp_34 = temp_17;
    temp_35 = fma(temp_28, temp_26, temp_27 * temp_23);
    temp_36 = intBitsToFloat(undef);
    temp_37 = temp_34;
    if (temp_14)
    {
        temp_36 = temp_34;
    }
    if (temp_14)
    {
        temp_33 = fma(temp_25, temp_32, sysCustomShaderUniformBlock0.data[42].x);
    }
    temp_38 = temp_33;
    temp_39 = temp_38;
    if (temp_14)
    {
        temp_37 = temp_38;
    }
    temp_40 = temp_37;
    temp_41 = temp_40;
    if (temp_14)
    {
        temp_39 = sin(temp_36);
    }
    temp_42 = temp_39;
    temp_43 = temp_42;
    if (temp_14)
    {
        temp_41 = sin(temp_40);
    }
    temp_44 = exp2(log2(clamp(fma(temp_30, temp_29, temp_35), 0.0, 1.0)) * sysCustomShaderUniformBlock1.data[4].x);
    if (temp_14)
    {
        temp_43 = temp_42 * temp_41;
    }
    temp_45 = temp_43;
    if (temp_14)
    {
        temp_20 = fma(temp_44, sysCustomShaderUniformBlock0.data[41].y, temp_18);
    }
    temp_46 = temp_20;
    temp_47 = temp_46;
    if (temp_14)
    {
        temp_31 = fma(temp_44, sysCustomShaderUniformBlock0.data[41].y, temp_25);
    }
    if (temp_14)
    {
        temp_47 = fma(temp_45, sysCustomShaderUniformBlock0.data[41].w, temp_46);
    }
    temp_48 = temp_47;
    temp_49 = temp_48;
    if (temp_14)
    {
        temp_24 = fma(temp_45, sysCustomShaderUniformBlock0.data[41].w, temp_31);
    }
    temp_50 = temp_24;
    temp_51 = temp_50;
    if (temp_14)
    {
        temp_49 = fma(temp_19, sysCustomShaderUniformBlock0.data[42].x, temp_48);
    }
    if (temp_14)
    {
        temp_51 = texture(sysCustomShaderTextureSampler3, vec2(temp_50, temp_49)).x;
    }
    temp_52 = in_attr9.z;
    temp_53 = in_attr9.x;
    temp_54 = in_attr9.y;
    temp_55 = fma(temp_30, NnVfx2ViewParam.data[0].z, fma(temp_28, NnVfx2ViewParam.data[0].y, temp_27 * NnVfx2ViewParam.data[0].x));
    temp_56 = clamp(clamp(min(temp_44, 0.7) + -0.0, 0.0, 1.0) * sysCustomShaderUniformBlock1.data[4].z, 0.0, 1.0);
    temp_57 = inversesqrt(fma(temp_53, temp_53, temp_52 * temp_52));
    temp_58 = temp_53 * temp_57;
    temp_59 = temp_52 * (0.0 - temp_57);
    temp_60 = temp_54 * (0.0 - temp_58);
    temp_61 = temp_54 * (0.0 - temp_59);
    temp_62 = fma(temp_52, (0.0 - temp_59), (0.0 - temp_53 * (0.0 - temp_58)));
    temp_63 = inversesqrt(fma(temp_61, temp_61, fma(temp_62, temp_62, temp_60 * temp_60)));
    temp_64 = fma(temp_30, NnVfx2ViewParam.data[1].z, fma(temp_28, NnVfx2ViewParam.data[1].y, temp_27 * NnVfx2ViewParam.data[1].x));
    temp_65 = fma(temp_30, NnVfx2ViewParam.data[2].z, fma(temp_28, NnVfx2ViewParam.data[2].y, temp_27 * NnVfx2ViewParam.data[2].x));
    temp_66 = temp_63;
    if (temp_14)
    {
        temp_66 = 0.5;
    }
    temp_67 = fma(temp_58, temp_65, temp_59 * temp_55);
    temp_68 = fma(temp_65, temp_61 * (0.0 - temp_63), fma(temp_64, temp_62 * temp_63, temp_55 * temp_60 * temp_63));
    temp_69 = inversesqrt(fma(fma(temp_52, (0.0 - temp_65), fma(temp_54, (0.0 - temp_64), temp_53 * (0.0 - temp_55))), fma(temp_52, (0.0 - temp_65), fma(temp_54, (0.0 - temp_64), temp_53 * (0.0 - temp_55))), fma(temp_68, temp_68, temp_67 * temp_67)));
    temp_70 = in_attr0.x * fma(temp_56, fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].x), sysCustomShaderUniformBlock1.data[2].x), sysCustomShaderUniformBlock1.data[3].x * sysCustomShaderUniformBlock1.data[3].w);
    temp_71 = in_attr0.z * fma(temp_56, fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].z), sysCustomShaderUniformBlock1.data[2].z), sysCustomShaderUniformBlock1.data[3].z * sysCustomShaderUniformBlock1.data[3].w);
    temp_72 = in_attr0.y * fma(temp_56, fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].y), sysCustomShaderUniformBlock1.data[2].y), sysCustomShaderUniformBlock1.data[3].y * sysCustomShaderUniformBlock1.data[3].w);
    temp_73 = fma(temp_71, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_71);
    temp_74 = fma(temp_72, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_72);
    temp_75 = fma(temp_70, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_70);
    if (temp_14)
    {
        temp_76 = texture(sysCustomShaderTextureSampler4, vec2(temp_66, temp_51)).xyz;
        temp_73 = temp_76.z;
        temp_74 = temp_76.y;
        temp_75 = temp_76.x;
    }
    temp_77 = temp_73;
    temp_78 = temp_74;
    temp_79 = temp_75;
    temp_80 = texture(sysCustomShaderTextureArraySampler1, vec3(fma(temp_67 * temp_69, 0.5, 0.5), fma(temp_68 * temp_69, -0.5, 0.5), float(6))).xyz;
    temp_81 = in_attr7.x;
    temp_82 = in_attr7.z;
    temp_83 = fma(temp_28 + -1.0, 0.7, 1.0);
    temp_84 = temp_27 * 0.699999988;
    temp_85 = inversesqrt(fma(sysCustomShaderUniformBlock0.data[1].z, sysCustomShaderUniformBlock0.data[1].z, fma(sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].x * sysCustomShaderUniformBlock0.data[1].x)));
    temp_86 = temp_30 * 0.699999988;
    temp_87 = inversesqrt(fma(temp_86, temp_86, fma(temp_83, temp_83, temp_84 * temp_84)));
    temp_88 = temp_84 * temp_87;
    temp_89 = temp_83 * temp_87;
    temp_90 = temp_86 * temp_87;
    temp_91 = clamp(fma(temp_30, temp_85 * sysCustomShaderUniformBlock0.data[1].z, fma(temp_28, temp_85 * sysCustomShaderUniformBlock0.data[1].y, temp_27 * temp_85 * sysCustomShaderUniformBlock0.data[1].x)), 0.0, 1.0);
    temp_92 = temp_88 * temp_89;
    temp_93 = temp_89 * temp_90;
    temp_94 = uint(max(0, min(int(trunc((temp_82 + (0.0 - sysCustomShaderUniformBlock2.data[0x226].z)) * sysCustomShaderUniformBlock2.data[0x227].z)), 19)) * 20 + max(0, min(int(trunc((temp_81 + (0.0 - sysCustomShaderUniformBlock2.data[0x226].x)) * sysCustomShaderUniformBlock2.data[0x227].x)), 19)) << 4) >> 2;
    temp_95 = sysCustomShaderUniformBlock2.data[int(temp_94 >> 2)][int(temp_94) & 3];
    temp_96 = temp_90 * temp_90;
    temp_97 = temp_88 * temp_90;
    temp_98 = fma(temp_88, temp_88, (0.0 - temp_89 * temp_89));
    temp_99 = temp_91 + fma(temp_91, (0.0 - sysCustomShaderUniformBlock1.data[0].w), sysCustomShaderUniformBlock1.data[0].w);
    temp_100 = floatBitsToInt(temp_95);
    temp_101 = 0.0;
    temp_102 = 0.0;
    temp_103 = 0.0;
    temp_104 = 0.0;
    temp_105 = 0.0;
    temp_106 = 0.0;
    if (floatBitsToInt(temp_95) != -1)
    {
        temp_107 = max(sysCustomShaderUniformBlock1.data[0].x, 0.0001);
        temp_108 = fma(temp_107, 0.5, 0.5);
        temp_109 = temp_108 * 0.5 * temp_108;
        temp_110 = temp_107 * temp_107;
        temp_111 = 0;
        do
        {
            temp_112 = temp_100;
            temp_113 = temp_101;
            temp_114 = temp_102;
            temp_115 = temp_103;
            temp_116 = temp_112 & 255;
            temp_104 = temp_114;
            temp_105 = temp_115;
            temp_106 = temp_113;
            temp_117 = uint(temp_116) >= 30u;
            if (temp_117)
            {
                break;
            }
            temp_118 = temp_116 << 4;
            temp_119 = uint(temp_118 + 0x1CC0) >> 2;
            temp_120 = int(temp_119) + 1;
            temp_121 = uint(temp_118 + 0x1CC8) >> 2;
            temp_122 = uint(temp_118 + 0x1AE0) >> 2;
            temp_123 = int(temp_122) + 1;
            temp_124 = (0.0 - temp_81) + sysCustomShaderUniformBlock2.data[int(temp_119 >> 2)][int(temp_119) & 3];
            temp_125 = sysCustomShaderUniformBlock2.data[int(uint(temp_120) >> 2)][temp_120 & 3] + (0.0 - in_attr7.y);
            temp_126 = (0.0 - temp_82) + sysCustomShaderUniformBlock2.data[int(temp_121 >> 2)][int(temp_121) & 3];
            temp_127 = fma(temp_126, temp_126, fma(temp_125, temp_125, temp_124 * temp_124));
            temp_128 = uint(temp_118 + 0x2080) >> 2;
            temp_129 = temp_124 * inversesqrt(temp_127);
            temp_130 = uint(temp_118 + 0x1908) >> 2;
            temp_131 = temp_125 * inversesqrt(temp_127);
            temp_132 = temp_126 * inversesqrt(temp_127);
            temp_133 = uint(temp_118 + 0x1900) >> 2;
            temp_134 = int(temp_133) + 1;
            temp_135 = floatBitsToInt(sysCustomShaderUniformBlock2.data[int(temp_128 >> 2)][int(temp_128) & 3]) != 0;
            temp_136 = temp_127;
            if (!temp_135)
            {
                temp_136 = 1.0;
            }
            temp_137 = temp_136;
            if (temp_135)
            {
                temp_138 = uint(temp_118 + 0x1EA0) >> 2;
                temp_139 = int(temp_138) + 1;
                temp_140 = uint(temp_118 + 0x1EA8) >> 2;
                temp_141 = uint(temp_118 + 0x1AE8) >> 2;
                temp_142 = sysCustomShaderUniformBlock2.data[int(temp_141 >> 2)][int(temp_141) & 3];
                temp_143 = int(temp_141) + 1;
                temp_137 = exp2(sysCustomShaderUniformBlock2.data[int(uint(temp_143) >> 2)][temp_143 & 3] * log2(clamp(((0.0 - temp_142) + fma(temp_132, (0.0 - sysCustomShaderUniformBlock2.data[int(temp_140 >> 2)][int(temp_140) & 3]), fma(temp_131, (0.0 - sysCustomShaderUniformBlock2.data[int(uint(temp_139) >> 2)][temp_139 & 3]), temp_129 * (0.0 - sysCustomShaderUniformBlock2.data[int(temp_138 >> 2)][int(temp_138) & 3])))) * (1.0 / ((0.0 - temp_142) + 1.0)), 0.0, 1.0)));
            }
            temp_144 = temp_23 + temp_129;
            temp_145 = temp_26 + temp_131;
            temp_146 = temp_111 + 1;
            temp_147 = clamp(fma(temp_30, temp_132, fma(temp_28, temp_131, temp_27 * temp_129)), 0.0, 1.0) * exp2(sysCustomShaderUniformBlock2.data[int(uint(temp_123) >> 2)][temp_123 & 3] * log2(clamp(fma(sysCustomShaderUniformBlock2.data[int(temp_122 >> 2)][int(temp_122) & 3], (0.0 - sqrt(temp_127)), 1.0), 0.0, 1.0))) * temp_137;
            temp_148 = temp_29 + temp_132;
            temp_149 = sysCustomShaderUniformBlock2.data[int(temp_130 >> 2)][int(temp_130) & 3] * temp_147;
            temp_150 = inversesqrt(fma(temp_148, temp_148, fma(temp_145, temp_145, temp_144 * temp_144)));
            temp_151 = temp_144 * temp_150;
            temp_152 = temp_145 * temp_150;
            temp_153 = temp_148 * temp_150;
            temp_154 = max(fma(temp_30, temp_132, fma(temp_28, temp_131, temp_27 * temp_129)), 1E-08);
            temp_155 = max(fma(temp_30, temp_153, fma(temp_28, temp_152, temp_27 * temp_151)), 1E-08) * max(fma(temp_30, temp_153, fma(temp_28, temp_152, temp_27 * temp_151)), 1E-08);
            temp_156 = max(fma(temp_29, temp_153, fma(temp_26, temp_152, temp_23 * temp_151)), 1E-08);
            temp_157 = sysCustomShaderUniformBlock2.data[int(temp_133 >> 2)][int(temp_133) & 3] * temp_147;
            temp_158 = sysCustomShaderUniformBlock2.data[int(uint(temp_134) >> 2)][temp_134 & 3] * temp_147;
            temp_159 = (fma(exp2(temp_156 * fma(temp_156, -5.55473, -6.98316002)), (0.0 - sysCustomShaderUniformBlock1.data[0].z), exp2(temp_156 * fma(temp_156, -5.55473, -6.98316002))) + sysCustomShaderUniformBlock1.data[0].z) * 1.0 / (temp_109 + fma(max(fma(temp_30, temp_29, temp_35), 1E-08), (0.0 - temp_109), max(fma(temp_30, temp_29, temp_35), 1E-08))) * (1.0 / (temp_109 + fma(temp_109, (0.0 - temp_154), temp_154))) * temp_110 * (1.0 / max(fma(temp_155, temp_110 * temp_110, (0.0 - temp_155)) + 1.0, 1E-08)) * temp_110 * (1.0 / max(fma(temp_155, temp_110 * temp_110, (0.0 - temp_155)) + 1.0, 1E-08));
            temp_160 = fma(temp_157 * temp_159, 0.07957747, fma(temp_157, temp_79 * 0.318309873, temp_114));
            temp_161 = fma(temp_158 * temp_159, 0.07957747, fma(temp_158, temp_78 * 0.318309873, temp_115));
            temp_162 = fma(temp_149 * temp_159, 0.07957747, fma(temp_149, temp_77 * 0.318309873, temp_113));
            temp_100 = int(uint(temp_112) >> 8);
            temp_111 = temp_146;
            temp_101 = temp_162;
            temp_102 = temp_160;
            temp_103 = temp_161;
            temp_104 = temp_160;
            temp_105 = temp_161;
            temp_106 = temp_162;
        }
        while (!(temp_146 >= 4));
    }
    temp_117 = false;
    temp_163 = fma(temp_70, sysCustomShaderUniformBlock1.data[2].w, fma(temp_80.x, sysCustomShaderUniformBlock1.data[0].z, fma(temp_99 * sysCustomShaderUniformBlock0.data[0].x * temp_79, 0.31830987, max(0.0, fma(temp_98, sysCustomShaderUniformBlock0.data[29].x, fma(temp_90, sysCustomShaderUniformBlock0.data[23].z, fma(temp_89, sysCustomShaderUniformBlock0.data[23].y, temp_88 * sysCustomShaderUniformBlock0.data[23].x)) + sysCustomShaderUniformBlock0.data[23].w + fma(temp_97, sysCustomShaderUniformBlock0.data[26].w, fma(temp_96, sysCustomShaderUniformBlock0.data[26].z, fma(temp_93, sysCustomShaderUniformBlock0.data[26].y, temp_92 * sysCustomShaderUniformBlock0.data[26].x))))) * fma(temp_79, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_79))) + temp_104);
    temp_164 = fma(temp_72, sysCustomShaderUniformBlock1.data[2].w, fma(temp_80.y, sysCustomShaderUniformBlock1.data[0].z, fma(temp_99 * sysCustomShaderUniformBlock0.data[0].y * temp_78, 0.31830987, max(0.0, fma(temp_98, sysCustomShaderUniformBlock0.data[29].y, fma(temp_90, sysCustomShaderUniformBlock0.data[24].z, fma(temp_89, sysCustomShaderUniformBlock0.data[24].y, temp_88 * sysCustomShaderUniformBlock0.data[24].x)) + sysCustomShaderUniformBlock0.data[24].w + fma(temp_97, sysCustomShaderUniformBlock0.data[27].w, fma(temp_96, sysCustomShaderUniformBlock0.data[27].z, fma(temp_93, sysCustomShaderUniformBlock0.data[27].y, temp_92 * sysCustomShaderUniformBlock0.data[27].x))))) * fma(temp_78, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_78))) + temp_105);
    temp_165 = fma(temp_71, sysCustomShaderUniformBlock1.data[2].w, fma(temp_80.z, sysCustomShaderUniformBlock1.data[0].z, fma(temp_99 * sysCustomShaderUniformBlock0.data[0].z * temp_77, 0.31830987, max(0.0, fma(temp_98, sysCustomShaderUniformBlock0.data[29].z, fma(temp_90, sysCustomShaderUniformBlock0.data[25].z, fma(temp_89, sysCustomShaderUniformBlock0.data[25].y, temp_88 * sysCustomShaderUniformBlock0.data[25].x)) + sysCustomShaderUniformBlock0.data[25].w + fma(temp_97, sysCustomShaderUniformBlock0.data[28].w, fma(temp_96, sysCustomShaderUniformBlock0.data[28].z, fma(temp_93, sysCustomShaderUniformBlock0.data[28].y, temp_92 * sysCustomShaderUniformBlock0.data[28].x))))) * fma(temp_77, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_77))) + temp_106);
    temp_166 = inversesqrt(fma(sysCustomShaderUniformBlock0.data[1].z, sysCustomShaderUniformBlock0.data[1].z, fma(sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].x * sysCustomShaderUniformBlock0.data[1].x)));
    temp_167 = in_attr3.x + (0.0 - NnVfx2ViewParam.data[29].x);
    temp_168 = in_attr3.y + (0.0 - NnVfx2ViewParam.data[29].y);
    temp_169 = in_attr3.z + (0.0 - NnVfx2ViewParam.data[29].z);
    temp_170 = fma(temp_169, temp_169, fma(temp_168, temp_168, temp_167 * temp_167));
    temp_171 = clamp(fma(in_attr5.x, sysCustomShaderUniformBlock0.data[37].y, sysCustomShaderUniformBlock0.data[37].x), 0.0, 1.0) * in_attr6.x;
    temp_172 = exp2(max(fma(fma(temp_166 * sysCustomShaderUniformBlock0.data[1].z, (0.0 - temp_169 * inversesqrt(temp_170)), fma(temp_166 * sysCustomShaderUniformBlock0.data[1].y, (0.0 - temp_168 * inversesqrt(temp_170)), temp_166 * sysCustomShaderUniformBlock0.data[1].x * (0.0 - temp_167 * inversesqrt(temp_170)))), (0.0 - sysCustomShaderUniformBlock0.data[35].y), sysCustomShaderUniformBlock0.data[35].y), 1E-08)) * exp2(log2(clamp(1.0 / NnVfx2ViewParam.data[30].w * sqrt(temp_170), 0.0, 1.0)) * sysCustomShaderUniformBlock0.data[35].x);
    temp_173 = fma((0.0 - temp_163) + sysCustomShaderUniformBlock0.data[36].x, temp_171, temp_163);
    temp_174 = fma((0.0 - temp_164) + sysCustomShaderUniformBlock0.data[36].y, temp_171, temp_164);
    temp_175 = fma((0.0 - temp_165) + sysCustomShaderUniformBlock0.data[36].z, temp_171, temp_165);
    temp_176 = clamp((0.0 - exp2(clamp(fma(sqrt(temp_170), sysCustomShaderUniformBlock0.data[33].y, sysCustomShaderUniformBlock0.data[33].x), 0.0, 1.0) * (0.0 - sysCustomShaderUniformBlock0.data[33].z) * 1.44269502)) + 1.0, 0.0, 1.0) * sysCustomShaderUniformBlock0.data[32].w;
    sysOutputColor0.x = fma((0.0 - temp_173) + fma(fma(temp_172 * sysCustomShaderUniformBlock0.data[34].x, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].x)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].x), temp_176, temp_173);
    sysOutputColor0.y = fma((0.0 - temp_174) + fma(fma(temp_172 * sysCustomShaderUniformBlock0.data[34].y, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].y)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].y), temp_176, temp_174);
    sysOutputColor0.z = fma((0.0 - temp_175) + fma(fma(temp_172 * sysCustomShaderUniformBlock0.data[34].z, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].z)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].z), temp_176, temp_175);
    sysOutputColor0.w = clamp(fma(clamp(in_attr0.w * in_attr2.w, 0.0, 1.0) * in_attr1.x, sysCustomShaderUniformBlock1.data[11].x, sysCustomShaderUniformBlock1.data[11].y), 0.0, 1.0);
    return;
}
