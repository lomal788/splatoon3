// static_grsn.bfsha model VfxGeneralShader program 1940 (frag)
// sampler sysCustomShaderTextureArraySampler1 -> loc 8 -> material sampler ?
// sampler sysCustomShaderTextureSampler1 -> loc 9 -> material sampler ?
// sampler sysCustomShaderTextureSampler2 -> loc 12 -> material sampler ?
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

layout (binding = 14, std140) uniform _sysCustomShaderUniformBlock0
{
    precise vec4 data[4096];
} sysCustomShaderUniformBlock0;

layout (binding = 1, std140) uniform _fp_c1
{
    precise vec4 data[4096];
} fp_c1;

layout (binding = 8, std140) uniform _NnVfx2ViewParam
{
    precise vec4 data[4096];
} NnVfx2ViewParam;

layout (binding = 0) uniform sampler2D sysTextureSampler0;
layout (binding = 1) uniform sampler2D sysTextureSampler1;
layout (binding = 2) uniform sampler2D sysCustomShaderTextureSampler3;
layout (binding = 3) uniform sampler2D sysCustomShaderTextureSampler1;
layout (binding = 4) uniform sampler2D sysCustomShaderTextureSampler2;
layout (binding = 5) uniform sampler2D sysCustomShaderTextureSampler4;
layout (binding = 6) uniform sampler2DArray sysCustomShaderTextureArraySampler1;
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
    precise vec4 temp_2;
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
    precise float temp_13;
    int temp_14;
    precise float temp_15;
    bool temp_16;
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
    precise vec2 temp_44;
    precise float temp_45;
    precise float temp_46;
    precise float temp_47;
    precise float temp_48;
    bool temp_49;
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
    precise vec2 temp_60;
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
    precise vec3 temp_91;
    precise float temp_92;
    precise float temp_93;
    precise float temp_94;
    precise vec3 temp_95;
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
    uint temp_118;
    precise float temp_119;
    precise float temp_120;
    precise float temp_121;
    precise float temp_122;
    int temp_123;
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
    int temp_134;
    int temp_135;
    precise float temp_136;
    precise float temp_137;
    precise float temp_138;
    int temp_139;
    bool temp_140;
    int temp_141;
    uint temp_142;
    int temp_143;
    uint temp_144;
    uint temp_145;
    int temp_146;
    uint temp_147;
    precise float temp_148;
    precise float temp_149;
    precise float temp_150;
    bool temp_151;
    precise float temp_152;
    precise float temp_153;
    precise float temp_154;
    uint temp_155;
    precise float temp_156;
    precise float temp_157;
    uint temp_158;
    int temp_159;
    precise float temp_160;
    uint temp_161;
    int temp_162;
    uint temp_163;
    uint temp_164;
    precise float temp_165;
    int temp_166;
    precise float temp_167;
    int temp_168;
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
    temp_140 = false;
    temp_0 = in_attr2.x;
    temp_1 = in_attr2.y;
    temp_2 = texture(sysTextureSampler0, vec2(temp_0, temp_1)).xyzw;
    temp_3 = in_attr5.w;
    temp_4 = in_attr4.x;
    temp_5 = temp_2.w * temp_3;
    temp_6 = clamp(temp_5 * in_attr0.w, 0.0, 1.0);
    temp_7 = temp_6 * temp_4;
    temp_8 = temp_7 <= sysEmitterStaticUniformBlock.data[138].z;
    temp_9 = floatBitsToInt(temp_3);
    temp_10 = floatBitsToInt(temp_6);
    temp_11 = floatBitsToInt(temp_0);
    temp_12 = floatBitsToInt(temp_1);
    temp_13 = temp_4;
    if (temp_8)
    {
        discard;
    }
    if (temp_8)
    {
        temp_9 = 0;
    }
    temp_14 = temp_9;
    temp_15 = intBitsToFloat(temp_14);
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
        sysOutputColor0.x = intBitsToFloat(temp_14);
        sysOutputColor0.y = intBitsToFloat(temp_10);
        sysOutputColor0.z = intBitsToFloat(temp_11);
        sysOutputColor0.w = intBitsToFloat(temp_12);
        return;
    }
    temp_16 = 0.0 < sysCustomShaderUniformBlock1.data[4].w;
    temp_17 = sysEmitterStaticUniformBlock.data[138].z + sysCustomShaderUniformBlock1.data[4].y;
    temp_18 = intBitsToFloat(undef);
    temp_19 = temp_17;
    if (temp_16)
    {
        temp_18 = in_attr13.y;
    }
    temp_20 = temp_18;
    temp_21 = intBitsToFloat(undef);
    temp_22 = temp_20;
    if (temp_16)
    {
        temp_21 = sysCustomShaderUniformBlock0.data[41].z;
    }
    temp_23 = temp_21;
    temp_24 = temp_23;
    if (temp_16)
    {
        temp_13 = in_attr13.x;
    }
    temp_25 = temp_13;
    temp_26 = temp_25;
    if (temp_16)
    {
        temp_15 = fma(temp_20, temp_23, sysCustomShaderUniformBlock0.data[42].x);
    }
    if (temp_16)
    {
        temp_24 = fma(temp_25, temp_23, sysCustomShaderUniformBlock0.data[42].x);
    }
    temp_27 = intBitsToFloat(undef);
    if (temp_16)
    {
        temp_27 = temp_15;
    }
    temp_28 = intBitsToFloat(undef);
    if (temp_16)
    {
        temp_28 = temp_24;
    }
    temp_29 = temp_28;
    temp_30 = intBitsToFloat(undef);
    temp_31 = temp_29;
    if (temp_16)
    {
        temp_30 = sin(temp_27);
    }
    temp_32 = temp_30;
    temp_33 = temp_32;
    if (temp_16)
    {
        temp_31 = sin(temp_29);
    }
    if (temp_16)
    {
        temp_19 = sysCustomShaderUniformBlock0.data[42].y;
    }
    temp_34 = (temp_5 + (0.0 - temp_17)) * (1.0 / ((0.0 - temp_17) + 1.0));
    if (temp_16)
    {
        temp_22 = fma(temp_34, sysCustomShaderUniformBlock0.data[41].y, temp_20);
    }
    temp_35 = temp_22;
    temp_36 = temp_35;
    if (temp_16)
    {
        temp_33 = temp_32 * temp_31;
    }
    temp_37 = temp_33;
    if (temp_16)
    {
        temp_26 = fma(temp_34, sysCustomShaderUniformBlock0.data[41].y, temp_25);
    }
    temp_38 = temp_26;
    temp_39 = temp_38;
    if (temp_16)
    {
        temp_36 = fma(temp_37, sysCustomShaderUniformBlock0.data[41].w, temp_35);
    }
    temp_40 = temp_36;
    temp_41 = temp_40;
    if (temp_16)
    {
        temp_39 = fma(temp_37, sysCustomShaderUniformBlock0.data[41].w, temp_38);
    }
    temp_42 = temp_39;
    temp_43 = temp_42;
    if (temp_16)
    {
        temp_41 = fma(temp_19, sysCustomShaderUniformBlock0.data[42].x, temp_40);
    }
    temp_44 = texture(sysTextureSampler1, vec2(in_attr2.z, in_attr2.w)).xy;
    if (temp_16)
    {
        temp_43 = texture(sysCustomShaderTextureSampler3, vec2(temp_42, temp_41)).x;
    }
    temp_45 = in_attr7.x;
    temp_46 = intBitsToFloat(undef);
    if (temp_16)
    {
        temp_46 = 0.5;
    }
    temp_47 = in_attr7.y;
    temp_48 = in_attr7.z;
    temp_49 = floatBitsToInt(fma(float((gl_FrontFacing ? -1 : 0)), -2.0, -1.0)) <= 0;
    temp_50 = 1.0 / in_attr3.w;
    temp_51 = temp_45;
    temp_52 = temp_47;
    temp_53 = temp_48;
    if (temp_49)
    {
        temp_51 = (0.0 - temp_45) + -0.0;
    }
    temp_54 = clamp(clamp(min(temp_34, 0.7) + -0.0, 0.0, 1.0) * sysCustomShaderUniformBlock1.data[4].z, 0.0, 1.0);
    temp_55 = in_attr15.z;
    if (temp_49)
    {
        temp_52 = (0.0 - temp_47) + -0.0;
    }
    if (temp_49)
    {
        temp_53 = (0.0 - temp_48) + -0.0;
    }
    temp_56 = in_attr15.x;
    temp_57 = fma(temp_2.y, in_attr0.y, in_attr1.y) * in_attr5.y * fma(fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].y), sysCustomShaderUniformBlock1.data[2].y), temp_54, sysCustomShaderUniformBlock1.data[3].y * sysCustomShaderUniformBlock1.data[3].w);
    temp_58 = fma(temp_2.x, in_attr0.x, in_attr1.x) * in_attr5.x * fma(fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].x), sysCustomShaderUniformBlock1.data[2].x), temp_54, sysCustomShaderUniformBlock1.data[3].x * sysCustomShaderUniformBlock1.data[3].w);
    temp_59 = fma(temp_2.z, in_attr0.z, in_attr1.z) * in_attr5.z * fma(fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].z), sysCustomShaderUniformBlock1.data[2].z), temp_54, sysCustomShaderUniformBlock1.data[3].z * sysCustomShaderUniformBlock1.data[3].w);
    temp_60 = texture(sysCustomShaderTextureSampler1, vec2(in_attr3.x * temp_50, in_attr3.y * temp_50)).xy;
    temp_61 = inversesqrt(fma(temp_56, temp_56, temp_55 * temp_55));
    temp_62 = temp_44.x * sysCustomShaderUniformBlock1.data[6].x;
    temp_63 = temp_44.y * sysCustomShaderUniformBlock1.data[6].x;
    temp_64 = in_attr15.y;
    temp_65 = temp_56 * temp_61;
    temp_66 = sqrt((0.0 - clamp(fma(temp_63, temp_63, temp_62 * temp_62), 0.0, 1.0)) + 1.0);
    temp_67 = fma(temp_66, temp_51, fma(temp_62, in_attr8.x, temp_63 * in_attr9.x));
    temp_68 = fma(temp_66, temp_52, fma(temp_62, in_attr8.y, temp_63 * in_attr9.y));
    temp_69 = fma(temp_66, temp_53, fma(temp_62, in_attr8.z, temp_63 * in_attr9.z));
    temp_70 = temp_55 * (0.0 - temp_61);
    temp_71 = temp_64 * (0.0 - temp_65);
    temp_72 = fma(temp_55, (0.0 - temp_70), (0.0 - temp_56 * (0.0 - temp_65)));
    temp_73 = temp_64 * (0.0 - temp_70);
    temp_74 = inversesqrt(fma(temp_69, temp_69, fma(temp_68, temp_68, temp_67 * temp_67)));
    temp_75 = inversesqrt(fma(temp_73, temp_73, fma(temp_72, temp_72, temp_71 * temp_71)));
    temp_76 = temp_67 * temp_74;
    temp_77 = temp_68 * temp_74;
    temp_78 = temp_69 * temp_74;
    temp_79 = in_attr6.x;
    temp_80 = fma(temp_78, NnVfx2ViewParam.data[0].z, fma(temp_77, NnVfx2ViewParam.data[0].y, temp_76 * NnVfx2ViewParam.data[0].x));
    temp_81 = fma(temp_78, NnVfx2ViewParam.data[1].z, fma(temp_77, NnVfx2ViewParam.data[1].y, temp_76 * NnVfx2ViewParam.data[1].x));
    temp_82 = in_attr6.z;
    temp_83 = fma(temp_78, NnVfx2ViewParam.data[2].z, fma(temp_77, NnVfx2ViewParam.data[2].y, temp_76 * NnVfx2ViewParam.data[2].x));
    temp_84 = in_attr6.y;
    temp_85 = fma(temp_65, temp_83, temp_70 * temp_80);
    temp_86 = fma(temp_83, temp_73 * (0.0 - temp_75), fma(temp_81, temp_72 * temp_75, temp_80 * temp_71 * temp_75));
    temp_87 = inversesqrt(fma(fma(temp_55, (0.0 - temp_83), fma(temp_64, (0.0 - temp_81), temp_56 * (0.0 - temp_80))), fma(temp_55, (0.0 - temp_83), fma(temp_64, (0.0 - temp_81), temp_56 * (0.0 - temp_80))), fma(temp_86, temp_86, temp_85 * temp_85)));
    temp_88 = fma(temp_58, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_58);
    temp_89 = fma(temp_57, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_57);
    temp_90 = fma(temp_59, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_59);
    if (temp_16)
    {
        temp_91 = texture(sysCustomShaderTextureSampler4, vec2(temp_46, temp_43)).xyz;
        temp_88 = temp_91.x;
        temp_89 = temp_91.y;
        temp_90 = temp_91.z;
    }
    temp_92 = temp_88;
    temp_93 = temp_89;
    temp_94 = temp_90;
    temp_95 = texture(sysCustomShaderTextureArraySampler1, vec3(fma(temp_85 * temp_87, 0.5, 0.5), fma(temp_86 * temp_87, -0.5, 0.5), float(6))).xyz;
    temp_96 = in_attr12.x;
    temp_97 = in_attr12.z;
    temp_98 = (0.0 - temp_79) + NnVfx2ViewParam.data[29].x;
    temp_99 = (0.0 - temp_84) + NnVfx2ViewParam.data[29].y;
    temp_100 = (0.0 - temp_82) + NnVfx2ViewParam.data[29].z;
    temp_101 = temp_76 * 0.699999988;
    temp_102 = inversesqrt(fma(temp_100, temp_100, fma(temp_99, temp_99, temp_98 * temp_98)));
    temp_103 = inversesqrt(fma(sysCustomShaderUniformBlock0.data[1].z, sysCustomShaderUniformBlock0.data[1].z, fma(sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].x * sysCustomShaderUniformBlock0.data[1].x)));
    temp_104 = temp_98 * temp_102;
    temp_105 = temp_99 * temp_102;
    temp_106 = temp_100 * temp_102;
    temp_107 = fma(temp_77 + -1.0, 0.7, 1.0);
    temp_108 = temp_78 * 0.699999988;
    temp_109 = inversesqrt(fma(temp_108, temp_108, fma(temp_107, temp_107, temp_101 * temp_101)));
    temp_110 = temp_101 * temp_109;
    temp_111 = temp_107 * temp_109;
    temp_112 = temp_108 * temp_109;
    temp_113 = clamp(fma(temp_78, temp_103 * sysCustomShaderUniformBlock0.data[1].z, fma(temp_77, temp_103 * sysCustomShaderUniformBlock0.data[1].y, temp_76 * temp_103 * sysCustomShaderUniformBlock0.data[1].x)), 0.0, 1.0);
    temp_114 = temp_110 * temp_111;
    temp_115 = temp_111 * temp_112;
    temp_116 = temp_112 * temp_112;
    temp_117 = temp_110 * temp_112;
    temp_118 = uint(max(0, min(int(trunc((temp_97 + (0.0 - sysCustomShaderUniformBlock2.data[0x226].z)) * sysCustomShaderUniformBlock2.data[0x227].z)), 19)) * 20 + max(0, min(int(trunc((temp_96 + (0.0 - sysCustomShaderUniformBlock2.data[0x226].x)) * sysCustomShaderUniformBlock2.data[0x227].x)), 19)) << 4) >> 2;
    temp_119 = sysCustomShaderUniformBlock2.data[int(temp_118 >> 2)][int(temp_118) & 3];
    temp_120 = fma(temp_110, temp_110, (0.0 - temp_111 * temp_111));
    temp_121 = temp_113 + fma(temp_113, (0.0 - sysCustomShaderUniformBlock1.data[0].w), sysCustomShaderUniformBlock1.data[0].w);
    temp_122 = clamp((0.0 - fma(texture(sysCustomShaderTextureSampler2, vec2(fma(temp_82, sysCustomShaderUniformBlock0.data[19].z, fma(temp_84, sysCustomShaderUniformBlock0.data[19].y, temp_79 * sysCustomShaderUniformBlock0.data[19].x)) + sysCustomShaderUniformBlock0.data[19].w, fma(temp_82, sysCustomShaderUniformBlock0.data[20].z, fma(temp_84, sysCustomShaderUniformBlock0.data[20].y, temp_79 * sysCustomShaderUniformBlock0.data[20].x)) + sysCustomShaderUniformBlock0.data[20].w)).x, (0.0 - sysCustomShaderUniformBlock0.data[22].x), sysCustomShaderUniformBlock0.data[22].x) + fma(clamp(in_attr14.x + sysCustomShaderUniformBlock0.data[22].y, 0.0, 1.0), (0.0 - temp_60.y) + (0.0 - clamp(temp_60.x + -0.0, 0.0, 1.0)) + 1.0, clamp(in_attr14.x + sysCustomShaderUniformBlock0.data[22].y, 0.0, 1.0))) + 1.0, 0.0, 1.0);
    temp_123 = floatBitsToInt(temp_119);
    temp_124 = 0.0;
    temp_125 = 0.0;
    temp_126 = 0.0;
    temp_127 = 0.0;
    temp_128 = 0.0;
    temp_129 = 0.0;
    if (floatBitsToInt(temp_119) != -1)
    {
        temp_130 = max(sysCustomShaderUniformBlock1.data[0].x, 0.0001);
        temp_131 = fma(temp_130, 0.5, 0.5);
        temp_132 = temp_130 * temp_130;
        temp_133 = temp_131 * 0.5 * temp_131;
        temp_134 = 0;
        do
        {
            temp_135 = temp_123;
            temp_136 = temp_124;
            temp_137 = temp_125;
            temp_138 = temp_126;
            temp_139 = temp_135 & 255;
            temp_127 = temp_136;
            temp_128 = temp_137;
            temp_129 = temp_138;
            temp_140 = uint(temp_139) >= 30u;
            if (temp_140)
            {
                break;
            }
            temp_141 = temp_139 << 4;
            temp_142 = uint(temp_141 + 0x1CC0) >> 2;
            temp_143 = int(temp_142) + 1;
            temp_144 = uint(temp_141 + 0x1CC8) >> 2;
            temp_145 = uint(temp_141 + 0x1AE0) >> 2;
            temp_146 = int(temp_145) + 1;
            temp_147 = uint(temp_141 + 0x2080) >> 2;
            temp_148 = (0.0 - temp_96) + sysCustomShaderUniformBlock2.data[int(temp_142 >> 2)][int(temp_142) & 3];
            temp_149 = sysCustomShaderUniformBlock2.data[int(uint(temp_143) >> 2)][temp_143 & 3] + (0.0 - in_attr12.y);
            temp_150 = (0.0 - temp_97) + sysCustomShaderUniformBlock2.data[int(temp_144 >> 2)][int(temp_144) & 3];
            temp_151 = floatBitsToInt(sysCustomShaderUniformBlock2.data[int(temp_147 >> 2)][int(temp_147) & 3]) != 0;
            temp_152 = fma(temp_150, temp_150, fma(temp_149, temp_149, temp_148 * temp_148));
            temp_153 = temp_152;
            if (!temp_151)
            {
                temp_153 = 1.0;
            }
            temp_154 = temp_148 * inversesqrt(temp_152);
            temp_155 = uint(temp_141 + 0x1908) >> 2;
            temp_156 = temp_149 * inversesqrt(temp_152);
            temp_157 = temp_150 * inversesqrt(temp_152);
            temp_158 = uint(temp_141 + 0x1900) >> 2;
            temp_159 = int(temp_158) + 1;
            temp_160 = temp_153;
            if (temp_151)
            {
                temp_161 = uint(temp_141 + 0x1EA0) >> 2;
                temp_162 = int(temp_161) + 1;
                temp_163 = uint(temp_141 + 0x1EA8) >> 2;
                temp_164 = uint(temp_141 + 0x1AE8) >> 2;
                temp_165 = sysCustomShaderUniformBlock2.data[int(temp_164 >> 2)][int(temp_164) & 3];
                temp_166 = int(temp_164) + 1;
                temp_160 = exp2(sysCustomShaderUniformBlock2.data[int(uint(temp_166) >> 2)][temp_166 & 3] * log2(clamp(((0.0 - temp_165) + fma(temp_157, (0.0 - sysCustomShaderUniformBlock2.data[int(temp_163 >> 2)][int(temp_163) & 3]), fma(temp_156, (0.0 - sysCustomShaderUniformBlock2.data[int(uint(temp_162) >> 2)][temp_162 & 3]), temp_154 * (0.0 - sysCustomShaderUniformBlock2.data[int(temp_161 >> 2)][int(temp_161) & 3])))) * (1.0 / ((0.0 - temp_165) + 1.0)), 0.0, 1.0)));
            }
            temp_167 = temp_104 + temp_154;
            temp_168 = temp_134 + 1;
            temp_169 = clamp(fma(temp_78, temp_157, fma(temp_77, temp_156, temp_76 * temp_154)), 0.0, 1.0) * exp2(sysCustomShaderUniformBlock2.data[int(uint(temp_146) >> 2)][temp_146 & 3] * log2(clamp(fma(sysCustomShaderUniformBlock2.data[int(temp_145 >> 2)][int(temp_145) & 3], (0.0 - sqrt(temp_152)), 1.0), 0.0, 1.0))) * temp_160;
            temp_170 = temp_105 + temp_156;
            temp_171 = sysCustomShaderUniformBlock2.data[int(temp_158 >> 2)][int(temp_158) & 3] * temp_169;
            temp_172 = temp_106 + temp_157;
            temp_173 = sysCustomShaderUniformBlock2.data[int(uint(temp_159) >> 2)][temp_159 & 3] * temp_169;
            temp_174 = sysCustomShaderUniformBlock2.data[int(temp_155 >> 2)][int(temp_155) & 3] * temp_169;
            temp_175 = max(fma(temp_78, temp_157, fma(temp_77, temp_156, temp_76 * temp_154)), 1E-08);
            temp_176 = inversesqrt(fma(temp_172, temp_172, fma(temp_170, temp_170, temp_167 * temp_167)));
            temp_177 = temp_167 * temp_176;
            temp_178 = temp_170 * temp_176;
            temp_179 = temp_172 * temp_176;
            temp_180 = max(fma(temp_106, temp_179, fma(temp_105, temp_178, temp_104 * temp_177)), 1E-08);
            temp_181 = max(fma(temp_78, temp_179, fma(temp_77, temp_178, temp_76 * temp_177)), 1E-08) * max(fma(temp_78, temp_179, fma(temp_77, temp_178, temp_76 * temp_177)), 1E-08);
            temp_182 = (fma(exp2(temp_180 * fma(temp_180, -5.55473, -6.98316002)), (0.0 - sysCustomShaderUniformBlock1.data[0].z), exp2(temp_180 * fma(temp_180, -5.55473, -6.98316002))) + sysCustomShaderUniformBlock1.data[0].z) * 1.0 / (temp_133 + fma(max(fma(temp_78, temp_106, fma(temp_77, temp_105, temp_76 * temp_104)), 1E-08), (0.0 - temp_133), max(fma(temp_78, temp_106, fma(temp_77, temp_105, temp_76 * temp_104)), 1E-08))) * (1.0 / (temp_133 + fma(temp_133, (0.0 - temp_175), temp_175))) * temp_132 * (1.0 / max(fma(temp_181, temp_132 * temp_132, (0.0 - temp_181)) + 1.0, 1E-08)) * temp_132 * (1.0 / max(fma(temp_181, temp_132 * temp_132, (0.0 - temp_181)) + 1.0, 1E-08));
            temp_183 = fma(temp_171 * temp_182, 0.07957747, fma(temp_171, temp_92 * 0.318309873, temp_136));
            temp_184 = fma(temp_173 * temp_182, 0.07957747, fma(temp_173, temp_93 * 0.318309873, temp_137));
            temp_185 = fma(temp_174 * temp_182, 0.07957747, fma(temp_174, temp_94 * 0.318309873, temp_138));
            temp_123 = int(uint(temp_135) >> 8);
            temp_134 = temp_168;
            temp_124 = temp_183;
            temp_125 = temp_184;
            temp_126 = temp_185;
            temp_127 = temp_183;
            temp_128 = temp_184;
            temp_129 = temp_185;
        }
        while (!(temp_168 >= 4));
    }
    temp_140 = false;
    temp_186 = fma(temp_58, sysCustomShaderUniformBlock1.data[2].w, fma(temp_95.x, sysCustomShaderUniformBlock1.data[0].z, fma(temp_122 * temp_121 * sysCustomShaderUniformBlock0.data[0].x * temp_92, 0.31830987, max(0.0, fma(temp_120, sysCustomShaderUniformBlock0.data[29].x, fma(temp_112, sysCustomShaderUniformBlock0.data[23].z, fma(temp_111, sysCustomShaderUniformBlock0.data[23].y, temp_110 * sysCustomShaderUniformBlock0.data[23].x)) + sysCustomShaderUniformBlock0.data[23].w + fma(temp_117, sysCustomShaderUniformBlock0.data[26].w, fma(temp_116, sysCustomShaderUniformBlock0.data[26].z, fma(temp_115, sysCustomShaderUniformBlock0.data[26].y, temp_114 * sysCustomShaderUniformBlock0.data[26].x))))) * fma(temp_92, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_92))) + temp_127);
    temp_187 = fma(temp_57, sysCustomShaderUniformBlock1.data[2].w, fma(temp_95.y, sysCustomShaderUniformBlock1.data[0].z, fma(temp_122 * temp_121 * sysCustomShaderUniformBlock0.data[0].y * temp_93, 0.31830987, max(0.0, fma(temp_120, sysCustomShaderUniformBlock0.data[29].y, fma(temp_112, sysCustomShaderUniformBlock0.data[24].z, fma(temp_111, sysCustomShaderUniformBlock0.data[24].y, temp_110 * sysCustomShaderUniformBlock0.data[24].x)) + sysCustomShaderUniformBlock0.data[24].w + fma(temp_117, sysCustomShaderUniformBlock0.data[27].w, fma(temp_116, sysCustomShaderUniformBlock0.data[27].z, fma(temp_115, sysCustomShaderUniformBlock0.data[27].y, temp_114 * sysCustomShaderUniformBlock0.data[27].x))))) * fma(temp_93, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_93))) + temp_128);
    temp_188 = fma(temp_59, sysCustomShaderUniformBlock1.data[2].w, fma(temp_95.z, sysCustomShaderUniformBlock1.data[0].z, fma(temp_122 * temp_121 * sysCustomShaderUniformBlock0.data[0].z * temp_94, 0.31830987, max(0.0, fma(temp_120, sysCustomShaderUniformBlock0.data[29].z, fma(temp_112, sysCustomShaderUniformBlock0.data[25].z, fma(temp_111, sysCustomShaderUniformBlock0.data[25].y, temp_110 * sysCustomShaderUniformBlock0.data[25].x)) + sysCustomShaderUniformBlock0.data[25].w + fma(temp_117, sysCustomShaderUniformBlock0.data[28].w, fma(temp_116, sysCustomShaderUniformBlock0.data[28].z, fma(temp_115, sysCustomShaderUniformBlock0.data[28].y, temp_114 * sysCustomShaderUniformBlock0.data[28].x))))) * fma(temp_94, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_94))) + temp_129);
    temp_189 = inversesqrt(fma(sysCustomShaderUniformBlock0.data[1].z, sysCustomShaderUniformBlock0.data[1].z, fma(sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].x * sysCustomShaderUniformBlock0.data[1].x)));
    temp_190 = in_attr6.x + (0.0 - NnVfx2ViewParam.data[29].x);
    temp_191 = in_attr6.y + (0.0 - NnVfx2ViewParam.data[29].y);
    temp_192 = in_attr6.z + (0.0 - NnVfx2ViewParam.data[29].z);
    temp_193 = fma(temp_192, temp_192, fma(temp_191, temp_191, temp_190 * temp_190));
    temp_194 = clamp(fma(in_attr10.x, sysCustomShaderUniformBlock0.data[37].y, sysCustomShaderUniformBlock0.data[37].x), 0.0, 1.0) * in_attr11.x;
    temp_195 = exp2(max(fma(fma(temp_189 * sysCustomShaderUniformBlock0.data[1].z, (0.0 - temp_192 * inversesqrt(temp_193)), fma(temp_189 * sysCustomShaderUniformBlock0.data[1].y, (0.0 - temp_191 * inversesqrt(temp_193)), temp_189 * sysCustomShaderUniformBlock0.data[1].x * (0.0 - temp_190 * inversesqrt(temp_193)))), (0.0 - sysCustomShaderUniformBlock0.data[35].y), sysCustomShaderUniformBlock0.data[35].y), 1E-08)) * exp2(log2(clamp(1.0 / NnVfx2ViewParam.data[30].w * sqrt(temp_193), 0.0, 1.0)) * sysCustomShaderUniformBlock0.data[35].x);
    temp_196 = fma((0.0 - temp_186) + sysCustomShaderUniformBlock0.data[36].x, temp_194, temp_186);
    temp_197 = fma((0.0 - temp_187) + sysCustomShaderUniformBlock0.data[36].y, temp_194, temp_187);
    temp_198 = fma((0.0 - temp_188) + sysCustomShaderUniformBlock0.data[36].z, temp_194, temp_188);
    temp_199 = clamp((0.0 - exp2(clamp(fma(sqrt(temp_193), sysCustomShaderUniformBlock0.data[33].y, sysCustomShaderUniformBlock0.data[33].x), 0.0, 1.0) * (0.0 - sysCustomShaderUniformBlock0.data[33].z) * 1.44269502)) + 1.0, 0.0, 1.0) * sysCustomShaderUniformBlock0.data[32].w;
    sysOutputColor0.x = fma((0.0 - temp_196) + fma(fma(temp_195 * sysCustomShaderUniformBlock0.data[34].x, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].x)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].x), temp_199, temp_196);
    sysOutputColor0.y = fma((0.0 - temp_197) + fma(fma(temp_195 * sysCustomShaderUniformBlock0.data[34].y, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].y)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].y), temp_199, temp_197);
    sysOutputColor0.z = fma((0.0 - temp_198) + fma(fma(temp_195 * sysCustomShaderUniformBlock0.data[34].z, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].z)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].z), temp_199, temp_198);
    sysOutputColor0.w = clamp(fma(temp_7, sysCustomShaderUniformBlock1.data[11].x, sysCustomShaderUniformBlock1.data[11].y), 0.0, 1.0);
    return;
}
