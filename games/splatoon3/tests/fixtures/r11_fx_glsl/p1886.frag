// static_grsn.bfsha model VfxGeneralShader program 1886 (frag)
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
    precise vec4 temp_0;
    precise float temp_1;
    precise float temp_2;
    precise float temp_3;
    precise float temp_4;
    bool temp_5;
    int temp_6;
    int temp_7;
    int temp_8;
    precise vec2 temp_9;
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
    bool temp_29;
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
    precise vec2 temp_93;
    precise float temp_94;
    precise float temp_95;
    precise float temp_96;
    precise float temp_97;
    precise float temp_98;
    precise vec3 temp_99;
    precise float temp_100;
    precise float temp_101;
    precise float temp_102;
    precise vec3 temp_103;
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
    uint temp_120;
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
    uint temp_148;
    precise float temp_149;
    precise float temp_150;
    precise float temp_151;
    bool temp_152;
    precise float temp_153;
    precise float temp_154;
    precise float temp_155;
    uint temp_156;
    precise float temp_157;
    precise float temp_158;
    uint temp_159;
    int temp_160;
    precise float temp_161;
    uint temp_162;
    int temp_163;
    uint temp_164;
    uint temp_165;
    precise float temp_166;
    int temp_167;
    precise float temp_168;
    int temp_169;
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
    temp_141 = false;
    temp_0 = texture(sysTextureSampler0, vec2(in_attr2.x, in_attr2.y)).xyzw;
    temp_1 = in_attr0.w;
    temp_2 = in_attr1.w;
    temp_3 = clamp(fma(temp_0.w, in_attr5.w, (0.0 - temp_1)) * temp_2, 0.0, 1.0);
    temp_4 = temp_3 * in_attr4.x;
    temp_5 = temp_4 <= sysEmitterStaticUniformBlock.data[138].z;
    temp_6 = floatBitsToInt(temp_3);
    temp_7 = floatBitsToInt(temp_1);
    temp_8 = floatBitsToInt(temp_2);
    if (temp_5)
    {
        discard;
    }
    temp_9 = texture(sysTextureSampler1, vec2(in_attr2.z, in_attr2.w)).xy;
    if (temp_5)
    {
        temp_6 = 0;
    }
    if (temp_5)
    {
        temp_7 = 0;
    }
    if (temp_5)
    {
        temp_8 = 0;
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
        sysOutputColor0.z = intBitsToFloat(temp_8);
        sysOutputColor0.w = intBitsToFloat(temp_10);
        return;
    }
    temp_11 = temp_9.x * sysCustomShaderUniformBlock1.data[6].x;
    temp_12 = in_attr7.x;
    temp_13 = temp_9.y * sysCustomShaderUniformBlock1.data[6].x;
    temp_14 = (0.0 - clamp(fma(temp_13, temp_13, temp_11 * temp_11), 0.0, 1.0)) + 1.0;
    temp_15 = in_attr7.y;
    temp_16 = in_attr7.z;
    temp_17 = in_attr6.y;
    temp_18 = in_attr6.z;
    temp_19 = floatBitsToInt(fma(float((gl_FrontFacing ? -1 : 0)), -2.0, -1.0)) <= 0;
    temp_20 = in_attr6.x;
    temp_21 = fma(temp_11, in_attr8.y, temp_13 * in_attr9.y);
    temp_22 = (0.0 - temp_17) + NnVfx2ViewParam.data[29].y;
    temp_23 = temp_12;
    temp_24 = temp_15;
    temp_25 = temp_16;
    temp_26 = temp_14;
    temp_27 = temp_21;
    temp_28 = sqrt(temp_14);
    if (temp_19)
    {
        temp_23 = (0.0 - temp_12) + -0.0;
    }
    if (temp_19)
    {
        temp_24 = (0.0 - temp_15) + -0.0;
    }
    if (temp_19)
    {
        temp_25 = (0.0 - temp_16) + -0.0;
    }
    temp_29 = 0.0 < sysCustomShaderUniformBlock1.data[4].w;
    temp_30 = fma(sqrt(temp_14), temp_23, fma(temp_11, in_attr8.x, temp_13 * in_attr9.x));
    temp_31 = fma(sqrt(temp_14), temp_24, temp_21);
    temp_32 = (0.0 - temp_18) + NnVfx2ViewParam.data[29].z;
    if (temp_29)
    {
        temp_26 = in_attr13.x;
    }
    temp_33 = temp_26;
    temp_34 = (0.0 - temp_20) + NnVfx2ViewParam.data[29].x;
    temp_35 = temp_33;
    if (temp_29)
    {
        temp_27 = sysCustomShaderUniformBlock0.data[42].y;
    }
    temp_36 = inversesqrt(fma(temp_32, temp_32, fma(temp_22, temp_22, temp_34 * temp_34)));
    temp_37 = temp_30 * temp_30;
    temp_38 = fma(sqrt(temp_14), temp_25, fma(temp_11, in_attr8.z, temp_13 * in_attr9.z));
    temp_39 = temp_37;
    if (temp_29)
    {
        temp_28 = in_attr13.y;
    }
    temp_40 = temp_28;
    temp_41 = temp_40;
    if (temp_29)
    {
        temp_39 = sysCustomShaderUniformBlock0.data[41].z;
    }
    temp_42 = temp_39;
    temp_43 = temp_34 * temp_36;
    temp_44 = inversesqrt(fma(temp_38, temp_38, fma(temp_31, temp_31, temp_37)));
    temp_45 = temp_22 * temp_36;
    temp_46 = temp_32 * temp_36;
    temp_47 = temp_30 * temp_44;
    temp_48 = temp_31 * temp_44;
    temp_49 = temp_38 * temp_44;
    temp_50 = temp_43 * temp_47;
    temp_51 = temp_44;
    temp_52 = temp_42;
    temp_53 = temp_50;
    if (temp_29)
    {
        temp_51 = fma(temp_40, temp_42, sysCustomShaderUniformBlock0.data[42].x);
    }
    temp_54 = temp_51;
    temp_55 = temp_54;
    if (temp_29)
    {
        temp_52 = fma(temp_33, temp_42, sysCustomShaderUniformBlock0.data[42].x);
    }
    temp_56 = temp_52;
    temp_57 = temp_56;
    if (temp_29)
    {
        temp_53 = temp_54;
    }
    if (temp_29)
    {
        temp_55 = temp_56;
    }
    temp_58 = temp_55;
    temp_59 = temp_58;
    if (temp_29)
    {
        temp_57 = sin(temp_53);
    }
    temp_60 = temp_57;
    temp_61 = temp_60;
    if (temp_29)
    {
        temp_59 = sin(temp_58);
    }
    temp_62 = log2(clamp(fma(temp_46, temp_49, fma(temp_45, temp_48, temp_50)), 0.0, 1.0));
    temp_63 = temp_62;
    if (temp_29)
    {
        temp_61 = temp_60 * temp_59;
    }
    temp_64 = temp_61;
    temp_65 = exp2(temp_62 * sysCustomShaderUniformBlock1.data[4].x);
    if (temp_29)
    {
        temp_41 = fma(temp_65, sysCustomShaderUniformBlock0.data[41].y, temp_40);
    }
    temp_66 = temp_41;
    temp_67 = temp_66;
    if (temp_29)
    {
        temp_35 = fma(temp_65, sysCustomShaderUniformBlock0.data[41].y, temp_33);
    }
    if (temp_29)
    {
        temp_67 = fma(temp_64, sysCustomShaderUniformBlock0.data[41].w, temp_66);
    }
    temp_68 = temp_67;
    temp_69 = temp_68;
    if (temp_29)
    {
        temp_63 = fma(temp_64, sysCustomShaderUniformBlock0.data[41].w, temp_35);
    }
    temp_70 = temp_63;
    temp_71 = temp_70;
    if (temp_29)
    {
        temp_69 = fma(temp_27, sysCustomShaderUniformBlock0.data[42].x, temp_68);
    }
    if (temp_29)
    {
        temp_71 = texture(sysCustomShaderTextureSampler3, vec2(temp_70, temp_69)).x;
    }
    temp_72 = in_attr15.z;
    temp_73 = in_attr15.x;
    temp_74 = in_attr15.y;
    temp_75 = 1.0 / in_attr3.w;
    temp_76 = inversesqrt(fma(temp_73, temp_73, temp_72 * temp_72));
    temp_77 = fma(temp_49, NnVfx2ViewParam.data[0].z, fma(temp_48, NnVfx2ViewParam.data[0].y, temp_47 * NnVfx2ViewParam.data[0].x));
    temp_78 = temp_73 * temp_76;
    temp_79 = temp_72 * (0.0 - temp_76);
    temp_80 = temp_74 * (0.0 - temp_78);
    temp_81 = fma(temp_72, (0.0 - temp_79), (0.0 - temp_73 * (0.0 - temp_78)));
    temp_82 = temp_74 * (0.0 - temp_79);
    temp_83 = inversesqrt(fma(temp_82, temp_82, fma(temp_81, temp_81, temp_80 * temp_80)));
    temp_84 = fma(temp_49, NnVfx2ViewParam.data[2].z, fma(temp_48, NnVfx2ViewParam.data[2].y, temp_47 * NnVfx2ViewParam.data[2].x));
    temp_85 = fma(temp_49, NnVfx2ViewParam.data[1].z, fma(temp_48, NnVfx2ViewParam.data[1].y, temp_47 * NnVfx2ViewParam.data[1].x));
    temp_86 = fma(temp_78, temp_84, temp_79 * temp_77);
    temp_87 = fma(temp_85, temp_81 * temp_83, temp_77 * temp_80 * temp_83);
    temp_88 = fma(temp_84, temp_82 * (0.0 - temp_83), temp_87);
    temp_89 = clamp(clamp(min(temp_65, 0.7) + -0.0, 0.0, 1.0) * sysCustomShaderUniformBlock1.data[4].z, 0.0, 1.0);
    temp_90 = inversesqrt(fma(fma(temp_72, (0.0 - temp_84), fma(temp_74, (0.0 - temp_85), temp_73 * (0.0 - temp_77))), fma(temp_72, (0.0 - temp_84), fma(temp_74, (0.0 - temp_85), temp_73 * (0.0 - temp_77))), fma(temp_88, temp_88, temp_86 * temp_86)));
    temp_91 = temp_87;
    if (temp_29)
    {
        temp_91 = 0.5;
    }
    temp_92 = fma(temp_0.x, in_attr0.x, in_attr1.x) * in_attr5.x * fma(temp_89, fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].x), sysCustomShaderUniformBlock1.data[2].x), sysCustomShaderUniformBlock1.data[3].w * sysCustomShaderUniformBlock1.data[3].x);
    temp_93 = texture(sysCustomShaderTextureSampler1, vec2(in_attr3.x * temp_75, in_attr3.y * temp_75)).xy;
    temp_94 = fma(temp_0.z, in_attr0.z, in_attr1.z) * in_attr5.z * fma(temp_89, fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].z), sysCustomShaderUniformBlock1.data[2].z), sysCustomShaderUniformBlock1.data[3].w * sysCustomShaderUniformBlock1.data[3].z);
    temp_95 = fma(temp_0.y, in_attr0.y, in_attr1.y) * in_attr5.y * fma(temp_89, fma(sysCustomShaderUniformBlock1.data[3].w, (0.0 - sysCustomShaderUniformBlock1.data[3].y), sysCustomShaderUniformBlock1.data[2].y), sysCustomShaderUniformBlock1.data[3].w * sysCustomShaderUniformBlock1.data[3].y);
    temp_96 = fma(temp_92, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_92);
    temp_97 = fma(temp_95, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_95);
    temp_98 = fma(temp_94, (0.0 - sysCustomShaderUniformBlock1.data[0].y), temp_94);
    if (temp_29)
    {
        temp_99 = texture(sysCustomShaderTextureSampler4, vec2(temp_91, temp_71)).xyz;
        temp_96 = temp_99.x;
        temp_97 = temp_99.y;
        temp_98 = temp_99.z;
    }
    temp_100 = temp_96;
    temp_101 = temp_97;
    temp_102 = temp_98;
    temp_103 = texture(sysCustomShaderTextureArraySampler1, vec3(fma(temp_86 * temp_90, 0.5, 0.5), fma(temp_88 * temp_90, -0.5, 0.5), float(6))).xyz;
    temp_104 = in_attr12.x;
    temp_105 = in_attr12.z;
    temp_106 = temp_47 * 0.699999988;
    temp_107 = fma(temp_48 + -1.0, 0.7, 1.0);
    temp_108 = temp_49 * 0.699999988;
    temp_109 = inversesqrt(fma(temp_108, temp_108, fma(temp_107, temp_107, temp_106 * temp_106)));
    temp_110 = inversesqrt(fma(sysCustomShaderUniformBlock0.data[1].z, sysCustomShaderUniformBlock0.data[1].z, fma(sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].x * sysCustomShaderUniformBlock0.data[1].x)));
    temp_111 = temp_106 * temp_109;
    temp_112 = temp_107 * temp_109;
    temp_113 = temp_108 * temp_109;
    temp_114 = temp_111 * temp_112;
    temp_115 = temp_112 * temp_113;
    temp_116 = temp_113 * temp_113;
    temp_117 = clamp(fma(temp_49, temp_110 * sysCustomShaderUniformBlock0.data[1].z, fma(temp_48, temp_110 * sysCustomShaderUniformBlock0.data[1].y, temp_47 * temp_110 * sysCustomShaderUniformBlock0.data[1].x)), 0.0, 1.0);
    temp_118 = fma(temp_111, temp_111, (0.0 - temp_112 * temp_112));
    temp_119 = temp_111 * temp_113;
    temp_120 = uint(max(0, min(int(trunc((temp_105 + (0.0 - sysCustomShaderUniformBlock2.data[0x226].z)) * sysCustomShaderUniformBlock2.data[0x227].z)), 19)) * 20 + max(0, min(int(trunc((temp_104 + (0.0 - sysCustomShaderUniformBlock2.data[0x226].x)) * sysCustomShaderUniformBlock2.data[0x227].x)), 19)) << 4) >> 2;
    temp_121 = sysCustomShaderUniformBlock2.data[int(temp_120 >> 2)][int(temp_120) & 3];
    temp_122 = temp_117 + fma(temp_117, (0.0 - sysCustomShaderUniformBlock1.data[0].w), sysCustomShaderUniformBlock1.data[0].w);
    temp_123 = clamp((0.0 - fma(texture(sysCustomShaderTextureSampler2, vec2(fma(temp_18, sysCustomShaderUniformBlock0.data[19].z, fma(temp_17, sysCustomShaderUniformBlock0.data[19].y, temp_20 * sysCustomShaderUniformBlock0.data[19].x)) + sysCustomShaderUniformBlock0.data[19].w, fma(temp_18, sysCustomShaderUniformBlock0.data[20].z, fma(temp_17, sysCustomShaderUniformBlock0.data[20].y, temp_20 * sysCustomShaderUniformBlock0.data[20].x)) + sysCustomShaderUniformBlock0.data[20].w)).x, (0.0 - sysCustomShaderUniformBlock0.data[22].x), sysCustomShaderUniformBlock0.data[22].x) + fma(clamp(in_attr14.x + sysCustomShaderUniformBlock0.data[22].y, 0.0, 1.0), (0.0 - temp_93.y) + (0.0 - clamp(temp_93.x + -0.0, 0.0, 1.0)) + 1.0, clamp(in_attr14.x + sysCustomShaderUniformBlock0.data[22].y, 0.0, 1.0))) + 1.0, 0.0, 1.0);
    temp_124 = floatBitsToInt(temp_121);
    temp_125 = 0.0;
    temp_126 = 0.0;
    temp_127 = 0.0;
    temp_128 = 0.0;
    temp_129 = 0.0;
    temp_130 = 0.0;
    if (floatBitsToInt(temp_121) != -1)
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
            temp_148 = uint(temp_142 + 0x2080) >> 2;
            temp_149 = (0.0 - temp_104) + sysCustomShaderUniformBlock2.data[int(temp_143 >> 2)][int(temp_143) & 3];
            temp_150 = sysCustomShaderUniformBlock2.data[int(uint(temp_144) >> 2)][temp_144 & 3] + (0.0 - in_attr12.y);
            temp_151 = (0.0 - temp_105) + sysCustomShaderUniformBlock2.data[int(temp_145 >> 2)][int(temp_145) & 3];
            temp_152 = floatBitsToInt(sysCustomShaderUniformBlock2.data[int(temp_148 >> 2)][int(temp_148) & 3]) != 0;
            temp_153 = fma(temp_151, temp_151, fma(temp_150, temp_150, temp_149 * temp_149));
            temp_154 = temp_153;
            if (!temp_152)
            {
                temp_154 = 1.0;
            }
            temp_155 = temp_149 * inversesqrt(temp_153);
            temp_156 = uint(temp_142 + 0x1908) >> 2;
            temp_157 = temp_150 * inversesqrt(temp_153);
            temp_158 = temp_151 * inversesqrt(temp_153);
            temp_159 = uint(temp_142 + 0x1900) >> 2;
            temp_160 = int(temp_159) + 1;
            temp_161 = temp_154;
            if (temp_152)
            {
                temp_162 = uint(temp_142 + 0x1EA0) >> 2;
                temp_163 = int(temp_162) + 1;
                temp_164 = uint(temp_142 + 0x1EA8) >> 2;
                temp_165 = uint(temp_142 + 0x1AE8) >> 2;
                temp_166 = sysCustomShaderUniformBlock2.data[int(temp_165 >> 2)][int(temp_165) & 3];
                temp_167 = int(temp_165) + 1;
                temp_161 = exp2(sysCustomShaderUniformBlock2.data[int(uint(temp_167) >> 2)][temp_167 & 3] * log2(clamp(((0.0 - temp_166) + fma(temp_158, (0.0 - sysCustomShaderUniformBlock2.data[int(temp_164 >> 2)][int(temp_164) & 3]), fma(temp_157, (0.0 - sysCustomShaderUniformBlock2.data[int(uint(temp_163) >> 2)][temp_163 & 3]), temp_155 * (0.0 - sysCustomShaderUniformBlock2.data[int(temp_162 >> 2)][int(temp_162) & 3])))) * (1.0 / ((0.0 - temp_166) + 1.0)), 0.0, 1.0)));
            }
            temp_168 = temp_43 + temp_155;
            temp_169 = temp_135 + 1;
            temp_170 = clamp(fma(temp_49, temp_158, fma(temp_48, temp_157, temp_47 * temp_155)), 0.0, 1.0) * exp2(sysCustomShaderUniformBlock2.data[int(uint(temp_147) >> 2)][temp_147 & 3] * log2(clamp(fma(sysCustomShaderUniformBlock2.data[int(temp_146 >> 2)][int(temp_146) & 3], (0.0 - sqrt(temp_153)), 1.0), 0.0, 1.0))) * temp_161;
            temp_171 = temp_45 + temp_157;
            temp_172 = sysCustomShaderUniformBlock2.data[int(temp_159 >> 2)][int(temp_159) & 3] * temp_170;
            temp_173 = temp_46 + temp_158;
            temp_174 = sysCustomShaderUniformBlock2.data[int(uint(temp_160) >> 2)][temp_160 & 3] * temp_170;
            temp_175 = sysCustomShaderUniformBlock2.data[int(temp_156 >> 2)][int(temp_156) & 3] * temp_170;
            temp_176 = max(fma(temp_49, temp_158, fma(temp_48, temp_157, temp_47 * temp_155)), 1E-08);
            temp_177 = inversesqrt(fma(temp_173, temp_173, fma(temp_171, temp_171, temp_168 * temp_168)));
            temp_178 = temp_168 * temp_177;
            temp_179 = temp_171 * temp_177;
            temp_180 = temp_173 * temp_177;
            temp_181 = max(fma(temp_46, temp_180, fma(temp_45, temp_179, temp_43 * temp_178)), 1E-08);
            temp_182 = max(fma(temp_49, temp_180, fma(temp_48, temp_179, temp_47 * temp_178)), 1E-08) * max(fma(temp_49, temp_180, fma(temp_48, temp_179, temp_47 * temp_178)), 1E-08);
            temp_183 = (fma(exp2(temp_181 * fma(temp_181, -5.55473, -6.98316002)), (0.0 - sysCustomShaderUniformBlock1.data[0].z), exp2(temp_181 * fma(temp_181, -5.55473, -6.98316002))) + sysCustomShaderUniformBlock1.data[0].z) * 1.0 / (temp_133 + fma(max(fma(temp_46, temp_49, fma(temp_45, temp_48, temp_43 * temp_47)), 1E-08), (0.0 - temp_133), max(fma(temp_46, temp_49, fma(temp_45, temp_48, temp_43 * temp_47)), 1E-08))) * (1.0 / (temp_133 + fma(temp_133, (0.0 - temp_176), temp_176))) * temp_134 * (1.0 / max(fma(temp_182, temp_134 * temp_134, (0.0 - temp_182)) + 1.0, 1E-08)) * temp_134 * (1.0 / max(fma(temp_182, temp_134 * temp_134, (0.0 - temp_182)) + 1.0, 1E-08));
            temp_184 = fma(temp_172 * temp_183, 0.07957747, fma(temp_172, temp_100 * 0.318309873, temp_137));
            temp_185 = fma(temp_174 * temp_183, 0.07957747, fma(temp_174, temp_101 * 0.318309873, temp_138));
            temp_186 = fma(temp_175 * temp_183, 0.07957747, fma(temp_175, temp_102 * 0.318309873, temp_139));
            temp_124 = int(uint(temp_136) >> 8);
            temp_135 = temp_169;
            temp_125 = temp_184;
            temp_126 = temp_185;
            temp_127 = temp_186;
            temp_128 = temp_184;
            temp_129 = temp_185;
            temp_130 = temp_186;
        }
        while (!(temp_169 >= 4));
    }
    temp_141 = false;
    temp_187 = fma(temp_92, sysCustomShaderUniformBlock1.data[2].w, fma(temp_103.x, sysCustomShaderUniformBlock1.data[0].z, fma(temp_123 * temp_122 * sysCustomShaderUniformBlock0.data[0].x * temp_100, 0.31830987, max(0.0, fma(temp_118, sysCustomShaderUniformBlock0.data[29].x, fma(temp_113, sysCustomShaderUniformBlock0.data[23].z, fma(temp_112, sysCustomShaderUniformBlock0.data[23].y, temp_111 * sysCustomShaderUniformBlock0.data[23].x)) + sysCustomShaderUniformBlock0.data[23].w + fma(temp_119, sysCustomShaderUniformBlock0.data[26].w, fma(temp_116, sysCustomShaderUniformBlock0.data[26].z, fma(temp_115, sysCustomShaderUniformBlock0.data[26].y, temp_114 * sysCustomShaderUniformBlock0.data[26].x))))) * fma(temp_100, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_100))) + temp_128);
    temp_188 = fma(temp_95, sysCustomShaderUniformBlock1.data[2].w, fma(temp_103.y, sysCustomShaderUniformBlock1.data[0].z, fma(temp_123 * temp_122 * sysCustomShaderUniformBlock0.data[0].y * temp_101, 0.31830987, max(0.0, fma(temp_118, sysCustomShaderUniformBlock0.data[29].y, fma(temp_113, sysCustomShaderUniformBlock0.data[24].z, fma(temp_112, sysCustomShaderUniformBlock0.data[24].y, temp_111 * sysCustomShaderUniformBlock0.data[24].x)) + sysCustomShaderUniformBlock0.data[24].w + fma(temp_119, sysCustomShaderUniformBlock0.data[27].w, fma(temp_116, sysCustomShaderUniformBlock0.data[27].z, fma(temp_115, sysCustomShaderUniformBlock0.data[27].y, temp_114 * sysCustomShaderUniformBlock0.data[27].x))))) * fma(temp_101, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_101))) + temp_129);
    temp_189 = fma(temp_94, sysCustomShaderUniformBlock1.data[2].w, fma(temp_103.z, sysCustomShaderUniformBlock1.data[0].z, fma(temp_123 * temp_122 * sysCustomShaderUniformBlock0.data[0].z * temp_102, 0.31830987, max(0.0, fma(temp_118, sysCustomShaderUniformBlock0.data[29].z, fma(temp_113, sysCustomShaderUniformBlock0.data[25].z, fma(temp_112, sysCustomShaderUniformBlock0.data[25].y, temp_111 * sysCustomShaderUniformBlock0.data[25].x)) + sysCustomShaderUniformBlock0.data[25].w + fma(temp_119, sysCustomShaderUniformBlock0.data[28].w, fma(temp_116, sysCustomShaderUniformBlock0.data[28].z, fma(temp_115, sysCustomShaderUniformBlock0.data[28].y, temp_114 * sysCustomShaderUniformBlock0.data[28].x))))) * fma(temp_102, (0.0 - sysCustomShaderUniformBlock1.data[0].z), temp_102))) + temp_130);
    temp_190 = inversesqrt(fma(sysCustomShaderUniformBlock0.data[1].z, sysCustomShaderUniformBlock0.data[1].z, fma(sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].y, sysCustomShaderUniformBlock0.data[1].x * sysCustomShaderUniformBlock0.data[1].x)));
    temp_191 = in_attr6.x + (0.0 - NnVfx2ViewParam.data[29].x);
    temp_192 = in_attr6.y + (0.0 - NnVfx2ViewParam.data[29].y);
    temp_193 = in_attr6.z + (0.0 - NnVfx2ViewParam.data[29].z);
    temp_194 = fma(temp_193, temp_193, fma(temp_192, temp_192, temp_191 * temp_191));
    temp_195 = clamp(fma(in_attr10.x, sysCustomShaderUniformBlock0.data[37].y, sysCustomShaderUniformBlock0.data[37].x), 0.0, 1.0) * in_attr11.x;
    temp_196 = exp2(max(fma(fma(temp_190 * sysCustomShaderUniformBlock0.data[1].z, (0.0 - temp_193 * inversesqrt(temp_194)), fma(temp_190 * sysCustomShaderUniformBlock0.data[1].y, (0.0 - temp_192 * inversesqrt(temp_194)), temp_190 * sysCustomShaderUniformBlock0.data[1].x * (0.0 - temp_191 * inversesqrt(temp_194)))), (0.0 - sysCustomShaderUniformBlock0.data[35].y), sysCustomShaderUniformBlock0.data[35].y), 1E-08)) * exp2(log2(clamp(1.0 / NnVfx2ViewParam.data[30].w * sqrt(temp_194), 0.0, 1.0)) * sysCustomShaderUniformBlock0.data[35].x);
    temp_197 = fma((0.0 - temp_187) + sysCustomShaderUniformBlock0.data[36].x, temp_195, temp_187);
    temp_198 = fma((0.0 - temp_188) + sysCustomShaderUniformBlock0.data[36].y, temp_195, temp_188);
    temp_199 = fma((0.0 - temp_189) + sysCustomShaderUniformBlock0.data[36].z, temp_195, temp_189);
    temp_200 = clamp((0.0 - exp2(clamp(fma(sqrt(temp_194), sysCustomShaderUniformBlock0.data[33].y, sysCustomShaderUniformBlock0.data[33].x), 0.0, 1.0) * (0.0 - sysCustomShaderUniformBlock0.data[33].z) * 1.44269502)) + 1.0, 0.0, 1.0) * sysCustomShaderUniformBlock0.data[32].w;
    sysOutputColor0.x = fma((0.0 - temp_197) + fma(fma(temp_196 * sysCustomShaderUniformBlock0.data[34].x, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].x)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].x), temp_200, temp_197);
    sysOutputColor0.y = fma((0.0 - temp_198) + fma(fma(temp_196 * sysCustomShaderUniformBlock0.data[34].y, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].y)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].y), temp_200, temp_198);
    sysOutputColor0.z = fma((0.0 - temp_199) + fma(fma(temp_196 * sysCustomShaderUniformBlock0.data[34].z, sysCustomShaderUniformBlock0.data[35].z, (0.0 - sysCustomShaderUniformBlock0.data[32].z)), sysCustomShaderUniformBlock0.data[33].w, sysCustomShaderUniformBlock0.data[32].z), temp_200, temp_199);
    sysOutputColor0.w = clamp(fma(temp_4, sysCustomShaderUniformBlock1.data[11].x, sysCustomShaderUniformBlock1.data[11].y), 0.0, 1.0);
    return;
}
