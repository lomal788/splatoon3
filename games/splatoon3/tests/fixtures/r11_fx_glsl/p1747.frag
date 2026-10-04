// static_grsn.bfsha model VfxGeneralShader program 1747 (frag)
// sampler sysCustomShaderTextureArraySampler1 -> loc 8 -> material sampler ?
// sampler sysCustomShaderTextureSampler3 -> loc 13 -> material sampler ?
// sampler sysCustomShaderTextureSampler4 -> loc 14 -> material sampler ?
// sampler sysTextureSampler0 -> loc 0 -> material sampler ?
// sampler sysTextureSampler1 -> loc 1 -> material sampler ?
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

layout (binding = 0) uniform sampler2D sysTextureSampler0;
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
    precise vec4 temp_0;
    precise float temp_1;
    precise float temp_2;
    precise float temp_3;
    precise float temp_4;
    bool temp_5;
    int temp_6;
    int temp_7;
    precise vec2 temp_8;
    int temp_9;
    int temp_10;
    precise float temp_11;
    precise float temp_12;
    precise float temp_13;
    precise float temp_14;
    precise float temp_15;
    precise float temp_16;
    precise float temp_17;
    precise float temp_18;
    bool temp_19;
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
    bool temp_30;
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
    precise vec3 temp_94;
    precise float temp_95;
    precise float temp_96;
    precise float temp_97;
    precise vec3 temp_98;
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
    uint temp_113;
    precise float temp_114;
    precise float temp_115;
    precise float temp_116;
    precise float temp_117;
    precise float temp_118;
    precise float temp_119;
    int temp_120;
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
    int temp_131;
    int temp_132;
    precise float temp_133;
    precise float temp_134;
    precise float temp_135;
    int temp_136;
    bool temp_137;
    int temp_138;
    uint temp_139;
    int temp_140;
    uint temp_141;
    uint temp_142;
    int temp_143;
    precise float temp_144;
    precise float temp_145;
    precise float temp_146;
    precise float temp_147;
    uint temp_148;
    precise float temp_149;
    precise float temp_150;
    precise float temp_151;
    uint temp_152;
    precise float temp_153;
    uint temp_154;
    int temp_155;
    bool temp_156;
    precise float temp_157;
    precise float temp_158;
    uint temp_159;
    int temp_160;
    uint temp_161;
    uint temp_162;
    precise float temp_163;
    int temp_164;
    precise float temp_165;
    int temp_166;
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
    temp_137 = false;
    temp_0 = texture(sysTextureSampler0, vec2(in_attr2.x, in_attr2.y)).xyzw;
    temp_1 = in_attr4.w;
    temp_2 = temp_0.w * temp_1;
    temp_3 = clamp(temp_2 * in_attr0.w, 0.0, 1.0);
    temp_4 = temp_3 * in_attr3.x;
    temp_5 = temp_4 <= sysEmitterStaticUniformBlock.data[138].z;
    temp_6 = floatBitsToInt(temp_1);
    temp_7 = floatBitsToInt(temp_3);
    if (temp_5)
    {
        discard;
    }
    temp_8 = texture(sysTextureSampler1, vec2(in_attr2.z, in_attr2.w)).xy;
    if (temp_5)
    {
        temp_6 = 0;
    }
    if (temp_5)
    {
        temp_7 = 0;
    }
    temp_9 = undef;
    if (temp_5)
    {
        temp_9 = 0;
    }
    temp_10 = undef;
    if (temp_5)
    {
        temp_10 = 0;
    }
    if (temp_5)
    {
        sysOutputColor0.x = intBitsToFloat(temp_6);
        sysOutputColor0.y = intBitsToFloat(temp_7);
        sysOutputColor0.z = intBitsToFloat(temp_9);
        sysOutputColor0.w = intBitsToFloat(temp_10);
        return;
    }
    temp_11 = temp_8.x * sysCustomShaderUniformBlock1.data[6].x;
    temp_12 = temp_8.y * sysCustomShaderUniformBlock1.data[6].x;
    temp_13 = in_attr6.x;
    temp_14 = in_attr6.y;
    temp_15 = in_attr6.z;
    temp_16 = in_attr7.z;
    temp_17 = sqrt((0.0 - clamp(fma(temp_12, temp_12, temp_11 * temp_11), 0.0, 1.0)) + 1.0);
    temp_18 = temp_12 * in_attr8.y;
    temp_19 = floatBitsToInt(fma(float((gl_FrontFacing ? -1 : 0)), -2.0, -1.0)) <= 0;
    temp_20 = fma(temp_11, in_attr7.y, temp_18);
    temp_21 = (0.0 - in_attr5.x) + NnVfx2ViewParam.data[29].x;
    temp_22 = (0.0 - in_attr5.y) + NnVfx2ViewParam.data[29].y;
    temp_23 = temp_13;
    temp_24 = temp_14;
    temp_25 = temp_17;
    temp_26 = temp_18;
    temp_27 = temp_20;
    temp_28 = temp_16;
    if (temp_19)
    {
        temp_23 = (0.0 - temp_13) + -0.0;
    }
    if (temp_19)
    {
        temp_24 = (0.0 - temp_14) + -0.0;
    }
    temp_29 = temp_15;
    if (temp_19)
    {
        temp_29 = (0.0 - temp_15) + -0.0;
    }
    temp_30 = 0.0 < sysCustomShaderUniformBlock1.data[4].w;
    temp_31 = fma(temp_17, temp_23, fma(temp_11, in_attr7.x, temp_12 * in_attr8.x));
    temp_32 = fma(temp_17, temp_24, temp_20);
    temp_33 = fma(temp_17, temp_29, fma(temp_11, temp_16, temp_12 * in_attr8.z));
    temp_34 = (0.0 - in_attr5.z) + NnVfx2ViewParam.data[29].z;
    temp_35 = inversesqrt(fma(temp_34, temp_34, fma(temp_22, temp_22, temp_21 * temp_21)));
    temp_36 = temp_31;
    temp_37 = temp_32;
    if (temp_30)
    {
        temp_25 = sysCustomShaderUniformBlock0.data[41].z;
    }
    temp_38 = temp_25;
    temp_39 = inversesqrt(fma(temp_33, temp_33, fma(temp_32, temp_32, temp_31 * temp_31)));
    temp_40 = temp_21 * temp_35;
    temp_41 = temp_22 * temp_35;
    temp_42 = temp_34 * temp_35;
    temp_43 = temp_31 * temp_39;
    if (temp_30)
    {
        temp_36 = in_attr12.x;
    }
    temp_44 = temp_36;
    temp_45 = temp_32 * temp_39;
    temp_46 = temp_44;
    if (temp_30)
    {
        temp_37 = in_attr12.y;
    }
    temp_47 = temp_37;
    temp_48 = temp_33 * temp_39;
    temp_49 = fma(temp_45, temp_41, temp_43 * temp_40);
    temp_50 = sysEmitterStaticUniformBlock.data[138].z + sysCustomShaderUniformBlock1.data[4].y;
    temp_51 = temp_2 + (0.0 - temp_50);
    temp_52 = 1.0 / ((0.0 - temp_50) + 1.0);
    temp_53 = temp_52;
    temp_54 = temp_47;
    temp_55 = temp_51;
    if (temp_30)
    {
        temp_26 = fma(temp_44, temp_38, sysCustomShaderUniformBlock0.data[42].x);
    }
    temp_56 = temp_26;
    temp_57 = temp_56;
    if (temp_30)
    {
        temp_27 = fma(temp_47, temp_38, sysCustomShaderUniformBlock0.data[42].x);
    }
    temp_58 = log2(clamp(fma(temp_48, temp_42, temp_49), 0.0, 1.0)) * sysCustomShaderUniformBlock1.data[4].x;
    temp_59 = temp_58;
    if (temp_30)
    {
        temp_28 = temp_56;
    }
    if (temp_30)
    {
        temp_57 = sin(temp_28);
    }
    temp_60 = temp_57;
    temp_61 = temp_60;
    if (temp_30)
    {
        temp_59 = sin(temp_27);
    }
    temp_62 = temp_59;
    temp_63 = temp_62;
    if (temp_30)
    {
        temp_53 = sysCustomShaderUniformBlock0.data[42].y;
    }
    if (temp_30)
    {
        temp_63 = temp_62 * temp_60;
    }
    temp_64 = temp_63;
    temp_65 = exp2(temp_58) * temp_51 * temp_52;
    if (temp_30)
    {
        temp_54 = fma(temp_65, sysCustomShaderUniformBlock0.data[41].y, temp_47);
    }
    temp_66 = temp_54;
    temp_67 = temp_66;
    if (temp_30)
    {
        temp_46 = fma(temp_65, sysCustomShaderUniformBlock0.data[41].y, temp_44);
    }
    if (temp_30)
    {
        temp_67 = fma(temp_64, sysCustomShaderUniformBlock0.data[41].w, temp_66);
    }
    if (temp_30)
    {
        temp_55 = fma(temp_64, sysCustomShaderUniformBlock0.data[41].w, temp_46);
    }
    temp_68 = temp_55;
    temp_69 = temp_68;
    if (temp_30)
    {
        temp_61 = fma(temp_53, sysCustomShaderUniformBlock0.data[42].x, temp_67);
    }
    if (temp_30)
    {
        temp_69 = texture(sysCustomShaderTextureSampler3, vec2(temp_68, temp_61)).x;
    }
    temp_70 = intBitsToFloat(undef);
    if (temp_30)
    {
        temp_70 = 0.5;
    }
    temp_71 = fma(temp_48, NnVfx2ViewParam.data[0].z, fma(temp_45, NnVfx2ViewParam.data[0].y, temp_43 * NnVfx2ViewParam.data[0].x));
    temp_72 = clamp(clamp(min(temp_65, 0.7) + -0.0, 0.0, 1.0) * sysCustomShaderUniformBlock1.data[4].z, 0.0, 1.0);
    temp_73 = in_attr13.z;
    temp_74 = in_attr13.x;
    temp_75 = in_attr13.y;
    temp_76 = inversesqrt(fma(temp_74, temp_74, temp_73 * temp_73));
    temp_77 = temp_74 * temp_76;
    temp_78 = temp_73 * (0.0 - temp_76);
    temp_79 = temp_75 * (0.0 - temp_77);
    temp_80 = fma(temp_73, (0.0 - temp_78), (0.0 - temp_74 * (0.0 - temp_77)));
    temp_81 = temp_75 * (0.0 - temp_78);
    temp_82 = inversesqrt(fma(temp_81, temp_81, fma(temp_80, temp_80, temp_79 * temp_79)));
    temp_83 = fma(temp_48, NnVfx2ViewParam.data[2].z, fma(temp_45, NnVfx2ViewParam.data[2].y, temp_43 * NnVfx2ViewParam.data[2].x));
    temp_84 = fma(temp_48, NnVfx2ViewParam.data[1].z, fma(temp_45, NnVfx2ViewParam.data[1].y, temp_43 * NnVfx2ViewParam.data[1].x));
    temp_85 = fma(temp_77, temp_83, temp_78 * temp_71);
    temp_86 = fma(temp_83, temp_81 * (0.0 - temp_82), fma(temp_84, temp_80 * temp_82, temp_71 * temp_79 * temp_82));
    temp_87 = inversesqrt(fma(fma(temp_73, (0.0 - temp_83), fma(temp_75, (0.0 - temp_84), temp_74 * (0.0 - temp_71))), fma(temp_73, (0.0 - temp_83), fma(temp_75, (0.0 - temp_84), temp_74 * (0.0 - temp_71))), fma(temp_86, temp_86, temp_85 * temp_85)));
    temp_88 = fma(temp_0.x, in_attr0.x, in_attr1.x) * fma(temp_72, fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].x), sysCustomShaderUniformBlock1.data[2].x), sysCustomShaderUniformBlock1.data[3].x * sysCustomShaderUniformBlock1.data[3].w);
    temp_89 = fma(temp_0.z, in_attr0.z, in_attr1.z) * fma(temp_72, fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].z), sysCustomShaderUniformBlock1.data[2].z), sysCustomShaderUniformBlock1.data[3].z * sysCustomShaderUniformBlock1.data[3].w);
    temp_90 = fma(temp_0.y, in_attr0.y, in_attr1.y) * fma(temp_72, fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].y), sysCustomShaderUniformBlock1.data[2].y), sysCustomShaderUniformBlock1.data[3].y * sysCustomShaderUniformBlock1.data[3].w);
    temp_91 = fma(temp_88, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_88);
    temp_92 = fma(temp_90, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_90);
    temp_93 = fma(temp_89, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_89);
    if (temp_30)
    {
        temp_94 = texture(sysCustomShaderTextureSampler4, vec2(temp_70, temp_69)).xyz;
        temp_91 = temp_94.x;
        temp_92 = temp_94.y;
        temp_93 = temp_94.z;
    }
    temp_95 = temp_91;
    temp_96 = temp_92;
    temp_97 = temp_93;
    temp_98 = texture(sysCustomShaderTextureArraySampler1, vec3(fma(temp_85 * temp_87, 0.5, 0.5), fma(temp_86 * temp_87, -0.5, 0.5), float(6))).xyz;
    temp_99 = in_attr11.x;
    temp_100 = in_attr11.z;
    temp_101 = temp_43 * 0.699999988;
    temp_102 = inversesqrt(fma(sysCustomShaderUniformBlock0.data[1].z, sysCustomShaderUniformBlock0.data[1].z, fma(sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].x * sysCustomShaderUniformBlock0.data[1].x)));
    temp_103 = fma(temp_45 + -1.0, 0.7, 1.0);
    temp_104 = temp_48 * 0.699999988;
    temp_105 = inversesqrt(fma(temp_104, temp_104, fma(temp_103, temp_103, temp_101 * temp_101)));
    temp_106 = temp_101 * temp_105;
    temp_107 = temp_103 * temp_105;
    temp_108 = temp_104 * temp_105;
    temp_109 = temp_106 * temp_107;
    temp_110 = clamp(fma(temp_48, temp_102 * sysCustomShaderUniformBlock0.data[1].z, fma(temp_45, temp_102 * sysCustomShaderUniformBlock0.data[1].y, temp_43 * temp_102 * sysCustomShaderUniformBlock0.data[1].x)), 0.0, 1.0);
    temp_111 = temp_107 * temp_108;
    temp_112 = temp_108 * temp_108;
    temp_113 = uint(max(0, min(int(trunc((temp_100 + (0.0 - sysCustomShaderUniformBlock2.data[0x226].z)) * sysCustomShaderUniformBlock2.data[0x227].z)), 19)) * 20 + max(0, min(int(trunc((temp_99 + (0.0 - sysCustomShaderUniformBlock2.data[0x226].x)) * sysCustomShaderUniformBlock2.data[0x227].x)), 19)) << 4) >> 2;
    temp_114 = sysCustomShaderUniformBlock2.data[int(temp_113 >> 2)][int(temp_113) & 3];
    temp_115 = temp_106 * temp_108;
    temp_116 = fma(temp_106, temp_106, (0.0 - temp_107 * temp_107));
    temp_117 = temp_110 + fma(temp_110, (0.0 - sysCustomShaderUniformBlock1.data[0].w), sysCustomShaderUniformBlock1.data[0].w);
    temp_118 = clamp(1.0 + (0.0 - sysCustomShaderUniformBlock1.data[1].x), 0.0, 1.0);
    temp_119 = fma(temp_4, sysCustomShaderUniformBlock1.data[11].x, sysCustomShaderUniformBlock1.data[11].y);
    temp_120 = floatBitsToInt(temp_114);
    temp_121 = 0.0;
    temp_122 = 0.0;
    temp_123 = 0.0;
    temp_124 = 0.0;
    temp_125 = 0.0;
    temp_126 = 0.0;
    if (floatBitsToInt(temp_114) != -1)
    {
        temp_127 = max(sysCustomShaderUniformBlock1.data[0].x, 0.0001);
        temp_128 = fma(temp_127, 0.5, 0.5);
        temp_129 = temp_128 * 0.5 * temp_128;
        temp_130 = temp_127 * temp_127;
        temp_131 = 0;
        do
        {
            temp_132 = temp_120;
            temp_133 = temp_121;
            temp_134 = temp_122;
            temp_135 = temp_123;
            temp_136 = temp_132 & 255;
            temp_124 = temp_133;
            temp_125 = temp_134;
            temp_126 = temp_135;
            temp_137 = uint(temp_136) >= 30u;
            if (temp_137)
            {
                break;
            }
            temp_138 = temp_136 << 4;
            temp_139 = uint(temp_138 + 0x1CC0) >> 2;
            temp_140 = int(temp_139) + 1;
            temp_141 = uint(temp_138 + 0x1CC8) >> 2;
            temp_142 = uint(temp_138 + 0x1AE0) >> 2;
            temp_143 = int(temp_142) + 1;
            temp_144 = (0.0 - temp_99) + sysCustomShaderUniformBlock2.data[int(temp_139 >> 2)][int(temp_139) & 3];
            temp_145 = sysCustomShaderUniformBlock2.data[int(uint(temp_140) >> 2)][temp_140 & 3] + (0.0 - in_attr11.y);
            temp_146 = (0.0 - temp_100) + sysCustomShaderUniformBlock2.data[int(temp_141 >> 2)][int(temp_141) & 3];
            temp_147 = fma(temp_146, temp_146, fma(temp_145, temp_145, temp_144 * temp_144));
            temp_148 = uint(temp_138 + 0x2080) >> 2;
            temp_149 = temp_145 * inversesqrt(temp_147);
            temp_150 = temp_146 * inversesqrt(temp_147);
            temp_151 = temp_144 * inversesqrt(temp_147);
            temp_152 = uint(temp_138 + 0x1908) >> 2;
            temp_153 = sysCustomShaderUniformBlock2.data[int(uint(temp_143) >> 2)][temp_143 & 3] * log2(clamp(fma(sysCustomShaderUniformBlock2.data[int(temp_142 >> 2)][int(temp_142) & 3], (0.0 - sqrt(temp_147)), 1.0), 0.0, 1.0));
            temp_154 = uint(temp_138 + 0x1900) >> 2;
            temp_155 = int(temp_154) + 1;
            temp_156 = floatBitsToInt(sysCustomShaderUniformBlock2.data[int(temp_148 >> 2)][int(temp_148) & 3]) != 0;
            temp_157 = temp_153;
            if (!temp_156)
            {
                temp_157 = 1.0;
            }
            temp_158 = temp_157;
            if (temp_156)
            {
                temp_159 = uint(temp_138 + 0x1EA0) >> 2;
                temp_160 = int(temp_159) + 1;
                temp_161 = uint(temp_138 + 0x1EA8) >> 2;
                temp_162 = uint(temp_138 + 0x1AE8) >> 2;
                temp_163 = sysCustomShaderUniformBlock2.data[int(temp_162 >> 2)][int(temp_162) & 3];
                temp_164 = int(temp_162) + 1;
                temp_158 = exp2(sysCustomShaderUniformBlock2.data[int(uint(temp_164) >> 2)][temp_164 & 3] * log2(clamp(((0.0 - temp_163) + fma(temp_150, (0.0 - sysCustomShaderUniformBlock2.data[int(temp_161 >> 2)][int(temp_161) & 3]), fma(temp_149, (0.0 - sysCustomShaderUniformBlock2.data[int(uint(temp_160) >> 2)][temp_160 & 3]), temp_151 * (0.0 - sysCustomShaderUniformBlock2.data[int(temp_159 >> 2)][int(temp_159) & 3])))) * (1.0 / ((0.0 - temp_163) + 1.0)), 0.0, 1.0)));
            }
            temp_165 = temp_40 + temp_151;
            temp_166 = temp_131 + 1;
            temp_167 = temp_41 + temp_149;
            temp_168 = clamp(fma(temp_48, temp_150, fma(temp_45, temp_149, temp_43 * temp_151)), 0.0, 1.0) * exp2(temp_153) * temp_158;
            temp_169 = temp_42 + temp_150;
            temp_170 = sysCustomShaderUniformBlock2.data[int(temp_154 >> 2)][int(temp_154) & 3] * temp_168;
            temp_171 = sysCustomShaderUniformBlock2.data[int(uint(temp_155) >> 2)][temp_155 & 3] * temp_168;
            temp_172 = sysCustomShaderUniformBlock2.data[int(temp_152 >> 2)][int(temp_152) & 3] * temp_168;
            temp_173 = max(fma(temp_48, temp_150, fma(temp_45, temp_149, temp_43 * temp_151)), 1E-08);
            temp_174 = inversesqrt(fma(temp_169, temp_169, fma(temp_167, temp_167, temp_165 * temp_165)));
            temp_175 = temp_165 * temp_174;
            temp_176 = temp_167 * temp_174;
            temp_177 = temp_169 * temp_174;
            temp_178 = max(fma(temp_42, temp_177, fma(temp_41, temp_176, temp_40 * temp_175)), 1E-08);
            temp_179 = max(fma(temp_48, temp_177, fma(temp_45, temp_176, temp_43 * temp_175)), 1E-08) * max(fma(temp_48, temp_177, fma(temp_45, temp_176, temp_43 * temp_175)), 1E-08);
            temp_180 = (fma(exp2(temp_178 * fma(temp_178, -5.55473, -6.98316002)), (0.0 - sysCustomShaderUniformBlock1.data[0].z), exp2(temp_178 * fma(temp_178, -5.55473, -6.98316002))) + sysCustomShaderUniformBlock1.data[0].z) * 1.0 / (temp_129 + fma(max(fma(temp_48, temp_42, temp_49), 1E-08), (0.0 - temp_129), max(fma(temp_48, temp_42, temp_49), 1E-08))) * (1.0 / (temp_129 + fma(temp_129, (0.0 - temp_173), temp_173))) * temp_130 * (1.0 / max(fma(temp_179, temp_130 * temp_130, (0.0 - temp_179)) + 1.0, 1E-08)) * temp_130 * (1.0 / max(fma(temp_179, temp_130 * temp_130, (0.0 - temp_179)) + 1.0, 1E-08));
            temp_181 = fma(temp_170 * temp_180, 0.07957747, fma(temp_170, temp_95 * 0.318309873, temp_133));
            temp_182 = fma(temp_171 * temp_180, 0.07957747, fma(temp_171, temp_96 * 0.318309873, temp_134));
            temp_183 = fma(temp_172 * temp_180, 0.07957747, fma(temp_172, temp_97 * 0.318309873, temp_135));
            temp_120 = int(uint(temp_132) >> 8);
            temp_131 = temp_166;
            temp_121 = temp_181;
            temp_122 = temp_182;
            temp_123 = temp_183;
            temp_124 = temp_181;
            temp_125 = temp_182;
            temp_126 = temp_183;
        }
        while (!(temp_166 >= 4));
    }
    temp_137 = false;
    temp_184 = inversesqrt(fma(sysCustomShaderUniformBlock0.data[1].z, sysCustomShaderUniformBlock0.data[1].z, fma(sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].x * sysCustomShaderUniformBlock0.data[1].x)));
    temp_185 = in_attr5.x + (0.0 - NnVfx2ViewParam.data[29].x);
    temp_186 = in_attr5.y + (0.0 - NnVfx2ViewParam.data[29].y);
    temp_187 = in_attr5.z + (0.0 - NnVfx2ViewParam.data[29].z);
    temp_188 = temp_184 * sysCustomShaderUniformBlock0.data[1].x;
    temp_189 = temp_184 * sysCustomShaderUniformBlock0.data[1].y;
    temp_190 = temp_184 * sysCustomShaderUniformBlock0.data[1].z;
    temp_191 = fma(temp_187, temp_187, fma(temp_186, temp_186, temp_185 * temp_185));
    temp_192 = (sysCustomShaderUniformBlock1.data[1].y + -1.0) * (sysCustomShaderUniformBlock1.data[1].y + -1.0);
    temp_193 = clamp(fma(in_attr9.x, sysCustomShaderUniformBlock0.data[37].y, sysCustomShaderUniformBlock0.data[37].x), 0.0, 1.0) * in_attr10.x;
    temp_194 = clamp(fma(temp_119, (0.0 - sysCustomShaderUniformBlock1.data[1].z), 1.0), 0.0, 1.0) * (fma(temp_192, -0.2, exp2(1.0 / sysCustomShaderUniformBlock1.data[1].y * log2(clamp(max(fma(temp_42, (0.0 - temp_190), fma(temp_41, (0.0 - temp_189), temp_40 * (0.0 - temp_188))), 0.001) + -0.0, 0.0, 1.0))) * temp_192) + 0.200000003);
    temp_195 = exp2(max(fma(fma(temp_190, (0.0 - temp_187 * inversesqrt(temp_191)), fma(temp_189, (0.0 - temp_186 * inversesqrt(temp_191)), temp_188 * (0.0 - temp_185 * inversesqrt(temp_191)))), (0.0 - sysCustomShaderUniformBlock0.data[35].y), sysCustomShaderUniformBlock0.data[35].y), 1E-08)) * exp2(log2(clamp(1.0 / NnVfx2ViewParam.data[30].w * sqrt(temp_191), 0.0, 1.0)) * sysCustomShaderUniformBlock0.data[35].x);
    temp_196 = fma(temp_88, sysCustomShaderUniformBlock1.data[2].w, fma(temp_194 * sqrt(temp_88) * sysCustomShaderUniformBlock0.data[0].w, sysCustomShaderUniformBlock1.data[1].x, fma(temp_98.x, sysCustomShaderUniformBlock1.data[0].z, fma(temp_117 * sysCustomShaderUniformBlock0.data[0].x * temp_95 * temp_118, 0.31830987, max(0.0, fma(temp_116, sysCustomShaderUniformBlock0.data[29].x, fma(temp_108, sysCustomShaderUniformBlock0.data[23].z, fma(temp_107, sysCustomShaderUniformBlock0.data[23].y, temp_106 * sysCustomShaderUniformBlock0.data[23].x)) + sysCustomShaderUniformBlock0.data[23].w + fma(temp_115, sysCustomShaderUniformBlock0.data[26].w, fma(temp_112, sysCustomShaderUniformBlock0.data[26].z, fma(temp_111, sysCustomShaderUniformBlock0.data[26].y, temp_109 * sysCustomShaderUniformBlock0.data[26].x))))) * fma(temp_95, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_95))) + temp_124));
    temp_197 = fma(temp_90, sysCustomShaderUniformBlock1.data[2].w, fma(temp_194 * sqrt(temp_90) * sysCustomShaderUniformBlock0.data[0].w, sysCustomShaderUniformBlock1.data[1].x, fma(temp_98.y, sysCustomShaderUniformBlock1.data[0].z, fma(temp_117 * sysCustomShaderUniformBlock0.data[0].y * temp_96 * temp_118, 0.31830987, max(0.0, fma(temp_116, sysCustomShaderUniformBlock0.data[29].y, fma(temp_108, sysCustomShaderUniformBlock0.data[24].z, fma(temp_107, sysCustomShaderUniformBlock0.data[24].y, temp_106 * sysCustomShaderUniformBlock0.data[24].x)) + sysCustomShaderUniformBlock0.data[24].w + fma(temp_115, sysCustomShaderUniformBlock0.data[27].w, fma(temp_112, sysCustomShaderUniformBlock0.data[27].z, fma(temp_111, sysCustomShaderUniformBlock0.data[27].y, temp_109 * sysCustomShaderUniformBlock0.data[27].x))))) * fma(temp_96, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_96))) + temp_125));
    temp_198 = fma(temp_89, sysCustomShaderUniformBlock1.data[2].w, fma(temp_194 * sqrt(temp_89) * sysCustomShaderUniformBlock0.data[0].w, sysCustomShaderUniformBlock1.data[1].x, fma(temp_98.z, sysCustomShaderUniformBlock1.data[0].z, fma(temp_117 * sysCustomShaderUniformBlock0.data[0].z * temp_97 * temp_118, 0.31830987, max(0.0, fma(temp_116, sysCustomShaderUniformBlock0.data[29].z, fma(temp_108, sysCustomShaderUniformBlock0.data[25].z, fma(temp_107, sysCustomShaderUniformBlock0.data[25].y, temp_106 * sysCustomShaderUniformBlock0.data[25].x)) + sysCustomShaderUniformBlock0.data[25].w + fma(temp_115, sysCustomShaderUniformBlock0.data[28].w, fma(temp_112, sysCustomShaderUniformBlock0.data[28].z, fma(temp_111, sysCustomShaderUniformBlock0.data[28].y, temp_109 * sysCustomShaderUniformBlock0.data[28].x))))) * fma(temp_97, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_97))) + temp_126));
    temp_199 = fma((0.0 - temp_197) + sysCustomShaderUniformBlock0.data[36].y, temp_193, temp_197);
    temp_200 = fma((0.0 - temp_196) + sysCustomShaderUniformBlock0.data[36].x, temp_193, temp_196);
    temp_201 = fma((0.0 - temp_198) + sysCustomShaderUniformBlock0.data[36].z, temp_193, temp_198);
    temp_202 = clamp((0.0 - exp2(clamp(fma(sqrt(temp_191), sysCustomShaderUniformBlock0.data[33].y, sysCustomShaderUniformBlock0.data[33].x), 0.0, 1.0) * (0.0 - sysCustomShaderUniformBlock0.data[33].z) * 1.44269502)) + 1.0, 0.0, 1.0) * sysCustomShaderUniformBlock0.data[32].w;
    sysOutputColor0.x = fma((0.0 - temp_200) + fma(fma(temp_195 * sysCustomShaderUniformBlock0.data[34].x, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].x)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].x), temp_202, temp_200);
    sysOutputColor0.y = fma((0.0 - temp_199) + fma(fma(temp_195 * sysCustomShaderUniformBlock0.data[34].y, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].y)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].y), temp_202, temp_199);
    sysOutputColor0.z = fma((0.0 - temp_201) + fma(fma(temp_195 * sysCustomShaderUniformBlock0.data[34].z, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].z)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].z), temp_202, temp_201);
    sysOutputColor0.w = clamp(temp_119 + -0.0, 0.0, 1.0);
    return;
}
