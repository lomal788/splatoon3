// static_grsn.bfsha model VfxGeneralShader program 1897 (frag)
// sampler sysCustomShaderTextureArraySampler1 -> loc 8 -> material sampler ?
// sampler sysCustomShaderTextureSampler3 -> loc 13 -> material sampler ?
// sampler sysCustomShaderTextureSampler4 -> loc 14 -> material sampler ?
// sampler sysDepthBufferTexture -> loc 4 -> material sampler ?
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

layout (binding = 0) uniform sampler2D sysDepthBufferTexture;
layout (binding = 1) uniform sampler2D sysTextureSampler0;
layout (binding = 2) uniform sampler2D sysTextureSampler1;
layout (binding = 3) uniform sampler2D sysCustomShaderTextureSampler3;
layout (binding = 4) uniform sampler2D sysCustomShaderTextureSampler4;
layout (binding = 5) uniform sampler2DArray sysCustomShaderTextureArraySampler1;
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
layout (location = 14) in vec4 in_attr14;
layout (location = 15) in vec4 in_attr15;

layout (location = 0) out vec4 sysOutputColor0;


void main()
{
    precise float temp_0;
    precise float temp_1;
    precise float temp_2;
    bool temp_3;
    int temp_4;
    precise float temp_5;
    precise float temp_6;
    precise float temp_7;
    precise float temp_8;
    precise float temp_9;
    precise float temp_10;
    int temp_11;
    int temp_12;
    int temp_13;
    precise float temp_14;
    bool temp_15;
    int temp_16;
    int temp_17;
    int temp_18;
    precise vec2 temp_19;
    precise float temp_20;
    precise float temp_21;
    precise float temp_22;
    precise float temp_23;
    precise float temp_24;
    precise float temp_25;
    bool temp_26;
    precise float temp_27;
    precise float temp_28;
    precise float temp_29;
    precise float temp_30;
    bool temp_31;
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
    precise vec3 temp_104;
    precise float temp_105;
    precise float temp_106;
    precise float temp_107;
    precise vec3 temp_108;
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
    precise float temp_120;
    precise float temp_121;
    precise float temp_122;
    uint temp_123;
    precise float temp_124;
    precise float temp_125;
    precise float temp_126;
    precise float temp_127;
    precise float temp_128;
    int temp_129;
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
    int temp_140;
    int temp_141;
    precise float temp_142;
    precise float temp_143;
    precise float temp_144;
    int temp_145;
    bool temp_146;
    int temp_147;
    uint temp_148;
    int temp_149;
    uint temp_150;
    uint temp_151;
    int temp_152;
    uint temp_153;
    precise float temp_154;
    precise float temp_155;
    precise float temp_156;
    bool temp_157;
    precise float temp_158;
    precise float temp_159;
    precise float temp_160;
    uint temp_161;
    precise float temp_162;
    precise float temp_163;
    uint temp_164;
    int temp_165;
    precise float temp_166;
    uint temp_167;
    int temp_168;
    uint temp_169;
    uint temp_170;
    precise float temp_171;
    int temp_172;
    precise float temp_173;
    int temp_174;
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
    temp_146 = false;
    temp_0 = 1.0 / (in_attr3.w * gl_FragCoord.w);
    temp_1 = in_attr0.x;
    temp_2 = clamp(fma(1.0 / fma(texture(sysDepthBufferTexture, vec2(in_attr3.x * gl_FragCoord.w * temp_0, in_attr3.y * gl_FragCoord.w * temp_0)).x, NnVfx2ViewParam.data[30].w, (0.0 - NnVfx2ViewParam.data[30].y)), (0.0 - NnVfx2ViewParam.data[30].z), (0.0 - 1.0 / fma(in_attr3.z * (1.0 / in_attr3.w), NnVfx2ViewParam.data[30].w, (0.0 - NnVfx2ViewParam.data[30].y)) * (0.0 - NnVfx2ViewParam.data[30].z))) * (1.0 / sysEmitterStaticUniformBlock.data[139].y), 0.0, 1.0) * clamp(fma(texture(sysTextureSampler0, vec2(in_attr2.x, in_attr2.y)).w, in_attr5.w, (0.0 - in_attr0.w)) * in_attr1.w, 0.0, 1.0) * in_attr4.x;
    temp_3 = temp_2 <= sysEmitterStaticUniformBlock.data[138].z;
    temp_4 = floatBitsToInt(temp_1);
    if (temp_3)
    {
        discard;
    }
    temp_5 = in_attr5.y * in_attr0.y;
    temp_6 = in_attr5.z * in_attr0.z;
    temp_7 = in_attr5.x * temp_1;
    temp_8 = temp_6;
    temp_9 = temp_7;
    temp_10 = temp_5;
    temp_11 = floatBitsToInt(temp_5);
    temp_12 = floatBitsToInt(temp_6);
    if (temp_3)
    {
        temp_4 = 0;
    }
    temp_13 = floatBitsToInt(temp_7);
    if (temp_3)
    {
        sysOutputColor0.x = temp_7;
        sysOutputColor0.y = temp_5;
        sysOutputColor0.z = temp_6;
        sysOutputColor0.w = intBitsToFloat(temp_4);
        return;
    }
    temp_14 = fma(temp_2, sysCustomShaderUniformBlock1.data[11].x, sysCustomShaderUniformBlock1.data[11].y);
    temp_15 = true;
    if (temp_14 <= sysEmitterStaticUniformBlock.data[138].z)
    {
        temp_15 = false;
        temp_8 = 0.0;
        temp_9 = 1.0;
        temp_10 = 0.0;
        temp_13 = 0x3F800000;
        temp_11 = 0;
        temp_12 = 0;
    }
    temp_16 = temp_13;
    temp_17 = temp_11;
    temp_18 = temp_12;
    if (temp_15)
    {
        temp_19 = texture(sysTextureSampler1, vec2(in_attr2.z, in_attr2.w)).xy;
        temp_20 = in_attr7.z;
        temp_21 = in_attr7.x;
        temp_22 = in_attr7.y;
        temp_23 = (0.0 - in_attr6.x) + NnVfx2ViewParam.data[29].x;
        temp_24 = (0.0 - in_attr6.y) + NnVfx2ViewParam.data[29].y;
        temp_25 = (0.0 - in_attr6.z) + NnVfx2ViewParam.data[29].z;
        temp_26 = floatBitsToInt(fma(float((gl_FrontFacing ? -1 : 0)), -2.0, -1.0)) <= 0;
        temp_27 = inversesqrt(fma(temp_25, temp_25, fma(temp_24, temp_24, temp_23 * temp_23)));
        temp_28 = temp_20;
        temp_29 = temp_21;
        temp_30 = temp_22;
        if (temp_26)
        {
            temp_28 = (0.0 - temp_20) + -0.0;
        }
        if (temp_26)
        {
            temp_29 = (0.0 - temp_21) + -0.0;
        }
        if (temp_26)
        {
            temp_30 = (0.0 - temp_22) + -0.0;
        }
        temp_31 = 0.0 < sysCustomShaderUniformBlock1.data[4].w;
        temp_32 = temp_23 * temp_27;
        temp_33 = temp_24 * temp_27;
        temp_34 = temp_25 * temp_27;
        temp_35 = temp_19.x * sysCustomShaderUniformBlock1.data[6].x;
        temp_36 = temp_19.y * sysCustomShaderUniformBlock1.data[6].x;
        temp_37 = temp_36 * in_attr9.z;
        temp_38 = fma(temp_35, in_attr8.y, temp_36 * in_attr9.y);
        temp_39 = fma(temp_35, in_attr8.z, temp_37);
        temp_40 = temp_37;
        temp_41 = temp_39;
        temp_42 = temp_38;
        if (temp_31)
        {
            temp_40 = in_attr14.y;
        }
        temp_43 = temp_40;
        temp_44 = sqrt((0.0 - clamp(fma(temp_36, temp_36, temp_35 * temp_35), 0.0, 1.0)) + 1.0);
        temp_45 = fma(temp_44, temp_29, fma(temp_35, in_attr8.x, temp_36 * in_attr9.x));
        temp_46 = fma(temp_44, temp_30, temp_38);
        temp_47 = fma(temp_44, temp_28, temp_39);
        temp_48 = temp_44;
        temp_49 = temp_46;
        temp_50 = temp_47;
        temp_51 = temp_43;
        if (temp_31)
        {
            temp_41 = in_attr14.x;
        }
        temp_52 = temp_41;
        temp_53 = temp_52;
        if (temp_31)
        {
            temp_48 = sysCustomShaderUniformBlock0.data[41].z;
        }
        temp_54 = temp_48;
        temp_55 = inversesqrt(fma(temp_47, temp_47, fma(temp_46, temp_46, temp_45 * temp_45)));
        temp_56 = temp_45 * temp_55;
        temp_57 = temp_46 * temp_55;
        temp_58 = temp_47 * temp_55;
        temp_59 = temp_54;
        if (temp_31)
        {
            temp_49 = fma(temp_43, temp_54, sysCustomShaderUniformBlock0.data[42].x);
        }
        temp_60 = temp_49;
        temp_61 = temp_60;
        if (temp_31)
        {
            temp_50 = fma(temp_52, temp_54, sysCustomShaderUniformBlock0.data[42].x);
        }
        temp_62 = temp_50;
        temp_63 = temp_62;
        if (temp_31)
        {
            temp_42 = temp_60;
        }
        if (temp_31)
        {
            temp_61 = temp_62;
        }
        temp_64 = temp_61;
        temp_65 = temp_64;
        if (temp_31)
        {
            temp_63 = sin(temp_42);
        }
        temp_66 = temp_63;
        temp_67 = fma(temp_57, temp_33, temp_56 * temp_32);
        temp_68 = temp_66;
        if (temp_31)
        {
            temp_65 = sin(temp_64);
        }
        temp_69 = log2(clamp(fma(temp_58, temp_34, temp_67), 0.0, 1.0));
        temp_70 = temp_69;
        if (temp_31)
        {
            temp_68 = temp_66 * temp_65;
        }
        temp_71 = temp_68;
        temp_72 = exp2(temp_69 * sysCustomShaderUniformBlock1.data[4].x);
        if (temp_31)
        {
            temp_70 = fma(temp_72, sysCustomShaderUniformBlock0.data[41].y, temp_43);
        }
        temp_73 = temp_70;
        temp_74 = temp_73;
        if (temp_31)
        {
            temp_53 = fma(temp_72, sysCustomShaderUniformBlock0.data[41].y, temp_52);
        }
        temp_75 = temp_53;
        temp_76 = temp_75;
        if (temp_31)
        {
            temp_51 = sysCustomShaderUniformBlock0.data[42].y;
        }
        if (temp_31)
        {
            temp_74 = fma(temp_71, sysCustomShaderUniformBlock0.data[41].w, temp_73);
        }
        if (temp_31)
        {
            temp_59 = fma(temp_71, sysCustomShaderUniformBlock0.data[41].w, temp_75);
        }
        temp_77 = temp_59;
        temp_78 = temp_77;
        if (temp_31)
        {
            temp_76 = fma(temp_51, sysCustomShaderUniformBlock0.data[42].x, temp_74);
        }
        if (temp_31)
        {
            temp_78 = texture(sysCustomShaderTextureSampler3, vec2(temp_77, temp_76)).x;
        }
        temp_79 = in_attr15.z;
        temp_80 = in_attr15.x;
        temp_81 = in_attr15.y;
        temp_82 = fma(temp_58, NnVfx2ViewParam.data[0].z, fma(temp_57, NnVfx2ViewParam.data[0].y, temp_56 * NnVfx2ViewParam.data[0].x));
        temp_83 = fma(temp_58, NnVfx2ViewParam.data[1].z, fma(temp_57, NnVfx2ViewParam.data[1].y, temp_56 * NnVfx2ViewParam.data[1].x));
        temp_84 = clamp(clamp(min(temp_72, 0.7) + -0.0, 0.0, 1.0) * sysCustomShaderUniformBlock1.data[4].z, 0.0, 1.0);
        temp_85 = inversesqrt(fma(temp_80, temp_80, temp_79 * temp_79));
        temp_86 = temp_80 * temp_85;
        temp_87 = temp_79 * (0.0 - temp_85);
        temp_88 = temp_81 * (0.0 - temp_86);
        temp_89 = temp_81 * (0.0 - temp_87);
        temp_90 = fma(temp_79, (0.0 - temp_87), (0.0 - temp_80 * (0.0 - temp_86)));
        temp_91 = inversesqrt(fma(temp_89, temp_89, fma(temp_90, temp_90, temp_88 * temp_88)));
        temp_92 = fma(temp_58, NnVfx2ViewParam.data[2].z, fma(temp_57, NnVfx2ViewParam.data[2].y, temp_56 * NnVfx2ViewParam.data[2].x));
        temp_93 = temp_82 * temp_88 * temp_91;
        temp_94 = fma(temp_86, temp_92, temp_87 * temp_82);
        temp_95 = temp_93;
        if (temp_31)
        {
            temp_95 = 0.5;
        }
        temp_96 = fma(temp_92, temp_89 * (0.0 - temp_91), fma(temp_83, temp_90 * temp_91, temp_93));
        temp_97 = inversesqrt(fma(fma(temp_79, (0.0 - temp_92), fma(temp_81, (0.0 - temp_83), temp_80 * (0.0 - temp_82))), fma(temp_79, (0.0 - temp_92), fma(temp_81, (0.0 - temp_83), temp_80 * (0.0 - temp_82))), fma(temp_96, temp_96, temp_94 * temp_94)));
        temp_98 = fma(temp_84, fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].z), sysCustomShaderUniformBlock1.data[2].z), sysCustomShaderUniformBlock1.data[3].w * sysCustomShaderUniformBlock1.data[3].z) * temp_8;
        temp_99 = fma(temp_84, fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].x), sysCustomShaderUniformBlock1.data[2].x), sysCustomShaderUniformBlock1.data[3].w * sysCustomShaderUniformBlock1.data[3].x) * temp_9;
        temp_100 = fma(temp_84, fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].y), sysCustomShaderUniformBlock1.data[2].y), sysCustomShaderUniformBlock1.data[3].w * sysCustomShaderUniformBlock1.data[3].y) * temp_10;
        temp_101 = fma(temp_99, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_99);
        temp_102 = fma(temp_98, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_98);
        temp_103 = fma(temp_100, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_100);
        if (temp_31)
        {
            temp_104 = texture(sysCustomShaderTextureSampler4, vec2(temp_95, temp_78)).xyz;
            temp_101 = temp_104.x;
            temp_102 = temp_104.z;
            temp_103 = temp_104.y;
        }
        temp_105 = temp_101;
        temp_106 = temp_102;
        temp_107 = temp_103;
        temp_108 = texture(sysCustomShaderTextureArraySampler1, vec3(fma(temp_94 * temp_97, 0.5, 0.5), fma(temp_96 * temp_97, -0.5, 0.5), float(6))).xyz;
        temp_109 = in_attr12.z;
        temp_110 = in_attr12.x;
        temp_111 = temp_56 * 0.699999988;
        temp_112 = temp_58 * 0.699999988;
        temp_113 = inversesqrt(fma(sysCustomShaderUniformBlock0.data[1].z, sysCustomShaderUniformBlock0.data[1].z, fma(sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].x * sysCustomShaderUniformBlock0.data[1].x)));
        temp_114 = fma(temp_57 + -1.0, 0.7, 1.0);
        temp_115 = inversesqrt(fma(temp_112, temp_112, fma(temp_114, temp_114, temp_111 * temp_111)));
        temp_116 = temp_111 * temp_115;
        temp_117 = temp_114 * temp_115;
        temp_118 = temp_112 * temp_115;
        temp_119 = temp_116 * temp_117;
        temp_120 = clamp(fma(temp_58, temp_113 * sysCustomShaderUniformBlock0.data[1].z, fma(temp_57, temp_113 * sysCustomShaderUniformBlock0.data[1].y, temp_56 * temp_113 * sysCustomShaderUniformBlock0.data[1].x)), 0.0, 1.0);
        temp_121 = temp_117 * temp_118;
        temp_122 = temp_118 * temp_118;
        temp_123 = uint(max(0, min(int(trunc((temp_109 + (0.0 - sysCustomShaderUniformBlock2.data[0x226].z)) * sysCustomShaderUniformBlock2.data[0x227].z)), 19)) * 20 + max(0, min(int(trunc((temp_110 + (0.0 - sysCustomShaderUniformBlock2.data[0x226].x)) * sysCustomShaderUniformBlock2.data[0x227].x)), 19)) << 4) >> 2;
        temp_124 = sysCustomShaderUniformBlock2.data[int(temp_123 >> 2)][int(temp_123) & 3];
        temp_125 = fma(temp_116, temp_116, (0.0 - temp_117 * temp_117));
        temp_126 = temp_116 * temp_118;
        temp_127 = in_attr13.x;
        temp_128 = temp_120 + fma(temp_120, (0.0 - sysCustomShaderUniformBlock1.data[0].w), sysCustomShaderUniformBlock1.data[0].w);
        temp_129 = floatBitsToInt(temp_124);
        temp_130 = 0.0;
        temp_131 = 0.0;
        temp_132 = 0.0;
        temp_133 = 0.0;
        temp_134 = 0.0;
        temp_135 = 0.0;
        if (floatBitsToInt(temp_124) != -1)
        {
            temp_136 = max(sysCustomShaderUniformBlock1.data[0].x, 0.0001);
            temp_137 = fma(temp_136, 0.5, 0.5);
            temp_138 = temp_137 * 0.5 * temp_137;
            temp_139 = temp_136 * temp_136;
            temp_140 = 0;
            do
            {
                temp_141 = temp_129;
                temp_142 = temp_130;
                temp_143 = temp_131;
                temp_144 = temp_132;
                temp_145 = temp_141 & 255;
                temp_133 = temp_142;
                temp_134 = temp_144;
                temp_135 = temp_143;
                temp_146 = uint(temp_145) >= 30u;
                if (temp_146)
                {
                    break;
                }
                temp_147 = temp_145 << 4;
                temp_148 = uint(temp_147 + 0x1CC0) >> 2;
                temp_149 = int(temp_148) + 1;
                temp_150 = uint(temp_147 + 0x1CC8) >> 2;
                temp_151 = uint(temp_147 + 0x1AE0) >> 2;
                temp_152 = int(temp_151) + 1;
                temp_153 = uint(temp_147 + 0x2080) >> 2;
                temp_154 = (0.0 - temp_110) + sysCustomShaderUniformBlock2.data[int(temp_148 >> 2)][int(temp_148) & 3];
                temp_155 = sysCustomShaderUniformBlock2.data[int(uint(temp_149) >> 2)][temp_149 & 3] + (0.0 - in_attr12.y);
                temp_156 = (0.0 - temp_109) + sysCustomShaderUniformBlock2.data[int(temp_150 >> 2)][int(temp_150) & 3];
                temp_157 = floatBitsToInt(sysCustomShaderUniformBlock2.data[int(temp_153 >> 2)][int(temp_153) & 3]) != 0;
                temp_158 = fma(temp_156, temp_156, fma(temp_155, temp_155, temp_154 * temp_154));
                temp_159 = temp_158;
                if (!temp_157)
                {
                    temp_159 = 1.0;
                }
                temp_160 = temp_154 * inversesqrt(temp_158);
                temp_161 = uint(temp_147 + 0x1908) >> 2;
                temp_162 = temp_155 * inversesqrt(temp_158);
                temp_163 = temp_156 * inversesqrt(temp_158);
                temp_164 = uint(temp_147 + 0x1900) >> 2;
                temp_165 = int(temp_164) + 1;
                temp_166 = temp_159;
                if (temp_157)
                {
                    temp_167 = uint(temp_147 + 0x1EA0) >> 2;
                    temp_168 = int(temp_167) + 1;
                    temp_169 = uint(temp_147 + 0x1EA8) >> 2;
                    temp_170 = uint(temp_147 + 0x1AE8) >> 2;
                    temp_171 = sysCustomShaderUniformBlock2.data[int(temp_170 >> 2)][int(temp_170) & 3];
                    temp_172 = int(temp_170) + 1;
                    temp_166 = exp2(sysCustomShaderUniformBlock2.data[int(uint(temp_172) >> 2)][temp_172 & 3] * log2(clamp(((0.0 - temp_171) + fma(temp_163, (0.0 - sysCustomShaderUniformBlock2.data[int(temp_169 >> 2)][int(temp_169) & 3]), fma(temp_162, (0.0 - sysCustomShaderUniformBlock2.data[int(uint(temp_168) >> 2)][temp_168 & 3]), temp_160 * (0.0 - sysCustomShaderUniformBlock2.data[int(temp_167 >> 2)][int(temp_167) & 3])))) * (1.0 / ((0.0 - temp_171) + 1.0)), 0.0, 1.0)));
                }
                temp_173 = temp_32 + temp_160;
                temp_174 = temp_140 + 1;
                temp_175 = clamp(fma(temp_58, temp_163, fma(temp_57, temp_162, temp_56 * temp_160)), 0.0, 1.0) * exp2(sysCustomShaderUniformBlock2.data[int(uint(temp_152) >> 2)][temp_152 & 3] * log2(clamp(fma(sysCustomShaderUniformBlock2.data[int(temp_151 >> 2)][int(temp_151) & 3], (0.0 - sqrt(temp_158)), 1.0), 0.0, 1.0))) * temp_166;
                temp_176 = temp_33 + temp_162;
                temp_177 = sysCustomShaderUniformBlock2.data[int(temp_164 >> 2)][int(temp_164) & 3] * temp_175;
                temp_178 = temp_34 + temp_163;
                temp_179 = sysCustomShaderUniformBlock2.data[int(uint(temp_165) >> 2)][temp_165 & 3] * temp_175;
                temp_180 = sysCustomShaderUniformBlock2.data[int(temp_161 >> 2)][int(temp_161) & 3] * temp_175;
                temp_181 = max(fma(temp_58, temp_163, fma(temp_57, temp_162, temp_56 * temp_160)), 1E-08);
                temp_182 = inversesqrt(fma(temp_178, temp_178, fma(temp_176, temp_176, temp_173 * temp_173)));
                temp_183 = temp_173 * temp_182;
                temp_184 = temp_176 * temp_182;
                temp_185 = temp_178 * temp_182;
                temp_186 = max(fma(temp_34, temp_185, fma(temp_33, temp_184, temp_32 * temp_183)), 1E-08);
                temp_187 = max(fma(temp_58, temp_185, fma(temp_57, temp_184, temp_56 * temp_183)), 1E-08) * max(fma(temp_58, temp_185, fma(temp_57, temp_184, temp_56 * temp_183)), 1E-08);
                temp_188 = (fma(exp2(temp_186 * fma(temp_186, -5.55473, -6.98316002)), (0.0 - sysCustomShaderUniformBlock1.data[0].z), exp2(temp_186 * fma(temp_186, -5.55473, -6.98316002))) + sysCustomShaderUniformBlock1.data[0].z) * 1.0 / (temp_138 + fma(max(fma(temp_58, temp_34, temp_67), 1E-08), (0.0 - temp_138), max(fma(temp_58, temp_34, temp_67), 1E-08))) * (1.0 / (temp_138 + fma(temp_138, (0.0 - temp_181), temp_181))) * temp_139 * (1.0 / max(fma(temp_187, temp_139 * temp_139, (0.0 - temp_187)) + 1.0, 1E-08)) * temp_139 * (1.0 / max(fma(temp_187, temp_139 * temp_139, (0.0 - temp_187)) + 1.0, 1E-08));
                temp_189 = fma(temp_177 * temp_188, 0.07957747, fma(temp_177, temp_105 * 0.318309873, temp_142));
                temp_190 = fma(temp_179 * temp_188, 0.07957747, fma(temp_179, temp_107 * 0.318309873, temp_143));
                temp_191 = fma(temp_180 * temp_188, 0.07957747, fma(temp_180, temp_106 * 0.318309873, temp_144));
                temp_129 = int(uint(temp_141) >> 8);
                temp_140 = temp_174;
                temp_130 = temp_189;
                temp_131 = temp_190;
                temp_132 = temp_191;
                temp_133 = temp_189;
                temp_134 = temp_191;
                temp_135 = temp_190;
            }
            while (!(temp_174 >= 4));
        }
        temp_146 = false;
        temp_192 = fma(temp_99, sysCustomShaderUniformBlock1.data[2].w, fma(temp_108.x, sysCustomShaderUniformBlock1.data[0].z, fma(temp_128 * sysCustomShaderUniformBlock0.data[0].x * temp_105 * temp_127, 0.31830987, max(0.0, fma(temp_125, sysCustomShaderUniformBlock0.data[29].x, fma(temp_118, sysCustomShaderUniformBlock0.data[23].z, fma(temp_117, sysCustomShaderUniformBlock0.data[23].y, temp_116 * sysCustomShaderUniformBlock0.data[23].x)) + sysCustomShaderUniformBlock0.data[23].w + fma(temp_126, sysCustomShaderUniformBlock0.data[26].w, fma(temp_122, sysCustomShaderUniformBlock0.data[26].z, fma(temp_121, sysCustomShaderUniformBlock0.data[26].y, temp_119 * sysCustomShaderUniformBlock0.data[26].x))))) * fma(temp_105, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_105))) + temp_133);
        temp_193 = fma(temp_98, sysCustomShaderUniformBlock1.data[2].w, fma(temp_108.z, sysCustomShaderUniformBlock1.data[0].z, fma(temp_128 * sysCustomShaderUniformBlock0.data[0].z * temp_106 * temp_127, 0.31830987, max(0.0, fma(temp_125, sysCustomShaderUniformBlock0.data[29].z, fma(temp_118, sysCustomShaderUniformBlock0.data[25].z, fma(temp_117, sysCustomShaderUniformBlock0.data[25].y, temp_116 * sysCustomShaderUniformBlock0.data[25].x)) + sysCustomShaderUniformBlock0.data[25].w + fma(temp_126, sysCustomShaderUniformBlock0.data[28].w, fma(temp_122, sysCustomShaderUniformBlock0.data[28].z, fma(temp_121, sysCustomShaderUniformBlock0.data[28].y, temp_119 * sysCustomShaderUniformBlock0.data[28].x))))) * fma(temp_106, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_106))) + temp_134);
        temp_194 = fma(temp_100, sysCustomShaderUniformBlock1.data[2].w, fma(temp_108.y, sysCustomShaderUniformBlock1.data[0].z, fma(temp_128 * sysCustomShaderUniformBlock0.data[0].y * temp_107 * temp_127, 0.31830987, max(0.0, fma(temp_125, sysCustomShaderUniformBlock0.data[29].y, fma(temp_118, sysCustomShaderUniformBlock0.data[24].z, fma(temp_117, sysCustomShaderUniformBlock0.data[24].y, temp_116 * sysCustomShaderUniformBlock0.data[24].x)) + sysCustomShaderUniformBlock0.data[24].w + fma(temp_126, sysCustomShaderUniformBlock0.data[27].w, fma(temp_122, sysCustomShaderUniformBlock0.data[27].z, fma(temp_121, sysCustomShaderUniformBlock0.data[27].y, temp_119 * sysCustomShaderUniformBlock0.data[27].x))))) * fma(temp_107, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_107))) + temp_135);
        temp_195 = inversesqrt(fma(sysCustomShaderUniformBlock0.data[1].z, sysCustomShaderUniformBlock0.data[1].z, fma(sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].x * sysCustomShaderUniformBlock0.data[1].x)));
        temp_196 = in_attr6.x + (0.0 - NnVfx2ViewParam.data[29].x);
        temp_197 = in_attr6.y + (0.0 - NnVfx2ViewParam.data[29].y);
        temp_198 = in_attr6.z + (0.0 - NnVfx2ViewParam.data[29].z);
        temp_199 = fma(temp_198, temp_198, fma(temp_197, temp_197, temp_196 * temp_196));
        temp_200 = clamp(fma(in_attr10.x, sysCustomShaderUniformBlock0.data[37].y, sysCustomShaderUniformBlock0.data[37].x), 0.0, 1.0) * in_attr11.x;
        temp_201 = exp2(max(fma(fma(temp_195 * sysCustomShaderUniformBlock0.data[1].z, (0.0 - temp_198 * inversesqrt(temp_199)), fma(temp_195 * sysCustomShaderUniformBlock0.data[1].y, (0.0 - temp_197 * inversesqrt(temp_199)), temp_195 * sysCustomShaderUniformBlock0.data[1].x * (0.0 - temp_196 * inversesqrt(temp_199)))), (0.0 - sysCustomShaderUniformBlock0.data[35].y), sysCustomShaderUniformBlock0.data[35].y), 1E-08)) * exp2(log2(clamp(1.0 / NnVfx2ViewParam.data[30].w * sqrt(temp_199), 0.0, 1.0)) * sysCustomShaderUniformBlock0.data[35].x);
        temp_202 = fma((0.0 - temp_192) + sysCustomShaderUniformBlock0.data[36].x, temp_200, temp_192);
        temp_203 = fma((0.0 - temp_194) + sysCustomShaderUniformBlock0.data[36].y, temp_200, temp_194);
        temp_204 = fma((0.0 - temp_193) + sysCustomShaderUniformBlock0.data[36].z, temp_200, temp_193);
        temp_205 = clamp((0.0 - exp2(clamp(fma(sqrt(temp_199), sysCustomShaderUniformBlock0.data[33].y, sysCustomShaderUniformBlock0.data[33].x), 0.0, 1.0) * (0.0 - sysCustomShaderUniformBlock0.data[33].z) * 1.44269502)) + 1.0, 0.0, 1.0) * sysCustomShaderUniformBlock0.data[32].w;
        temp_16 = floatBitsToInt(fma((0.0 - temp_202) + fma(fma(temp_201 * sysCustomShaderUniformBlock0.data[34].x, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].x)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].x), temp_205, temp_202));
        temp_17 = floatBitsToInt(fma((0.0 - temp_203) + fma(fma(temp_201 * sysCustomShaderUniformBlock0.data[34].y, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].y)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].y), temp_205, temp_203));
        temp_18 = floatBitsToInt(fma((0.0 - temp_204) + fma(fma(temp_201 * sysCustomShaderUniformBlock0.data[34].z, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].z)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].z), temp_205, temp_204));
    }
    sysOutputColor0.x = intBitsToFloat(temp_16);
    sysOutputColor0.y = intBitsToFloat(temp_17);
    sysOutputColor0.z = intBitsToFloat(temp_18);
    sysOutputColor0.w = clamp(temp_14 + -0.0, 0.0, 1.0);
    return;
}
