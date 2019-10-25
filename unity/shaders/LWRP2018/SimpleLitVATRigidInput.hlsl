#ifndef LIGHTWEIGHT_SIMPLE_LIT_VAT_INPUT_INCLUDED
#define LIGHTWEIGHT_SIMPLE_LIT_VAT_INPUT_INCLUDED

#include "Packages/com.unity.render-pipelines.lightweight/ShaderLibrary/Core.hlsl"
#include "Packages/com.unity.render-pipelines.lightweight/ShaderLibrary/SurfaceInput.hlsl"

CBUFFER_START(UnityPerMaterial)
float4 _MainTex_ST;
half4 _Color;
half4 _SpecColor;
half4 _EmissionColor;
half _Cutoff;
half _Shininess;

//--------------------------------------
// Declare shader properties
uniform float _boundingMax;
uniform float _boundingMin;
uniform float _boundingMax1;
uniform float _boundingMin1;
uniform int _numOfFrames;
uniform float _speed;
CBUFFER_END

TEXTURE2D(_posTex);
SAMPLER(sampler_posTex);
TEXTURE2D(_rotTex);
SAMPLER(sampler_rotTex);

struct VATAttributes
{
    float3 positionVAT;
    float3 normalVAT;
};

VATAttributes GetAttributesFromTexture(TEXTURE2D_ARGS(posTex, samplerPosTex), 
    TEXTURE2D_ARGS(rotTex, samplerRotTex), float4 uv, float4 uv2,
    float4 vertexCd, float4 vertexPos, float3 vertexN)
{
    VATAttributes output;
    float FPS = 24.0;
    float FPS_div_Frames = FPS / _numOfFrames;
    //Use the line below if you want to use time to animate the object
    float timeInFrames = frac(FPS_div_Frames * _speed * _Time.y);
    //The line below is particle age to drive the animation. Comment it out if you want to use time above.
    // timeInFrames = uv.z;

    timeInFrames = ceil(timeInFrames * _numOfFrames);
    timeInFrames /= _numOfFrames;
    timeInFrames += (1/_numOfFrames);

    //get position and rotation(quaternion) from textures
    float4 texturePos = SAMPLE_TEXTURE2D_LOD(posTex, samplerPosTex,
        float2(uv2.x, (1 - timeInFrames) + uv2.y),0);
    float4 textureRot = (SAMPLE_TEXTURE2D_LOD(rotTex, samplerRotTex, 
        float2(uv2.x, (1 - timeInFrames) + uv2.y),0));

    //expand normalised position texture values to world space
    float expand1 = _boundingMax1 - _boundingMin1;
    texturePos.xyz *= expand1;
    texturePos.xyz += _boundingMin1;
    texturePos.x *= -1;  //flipped to account for right-handedness of unity
    texturePos.xyz = texturePos.xzy;  //swizzle y and z because textures are exported with z-up

    //expand normalised pivot vertex colour values to world space
    float expand = _boundingMax - _boundingMin;
    float3 pivot = vertexCd.rgb;
    pivot.xyz *= expand;
    pivot.xyz += _boundingMin;
    pivot.x *=  -1;
    pivot = pivot.xzy;
    float3 atOrigin = vertexPos.xyz - pivot;

    //calculate rotation
    textureRot *= 2.0;
    textureRot -= 1.0;
    float4 quat = 0;

    //swizzle and flip quaternion from ue4 to unity
    quat.x = -textureRot.x;
    quat.y = textureRot.z;
    quat.z = textureRot.y;
    quat.w = textureRot.w;

    float3 rotated = atOrigin + 2.0 * cross(quat.xyz, cross(quat.xyz, atOrigin) + quat.w * atOrigin);

    output.positionVAT = rotated;
    output.positionVAT += pivot;
    output.positionVAT += texturePos;
    // output.positionVAT += center;

    //calculate normal
    float3 rotatedNormal = vertexN + 2.0 * cross(quat.xyz, cross(quat.xyz, vertexN) + quat.w * vertexN);
    output.normalVAT = rotatedNormal;

    return output;

}

TEXTURE2D(_SpecGlossMap);       SAMPLER(sampler_SpecGlossMap);

half4 SampleSpecularGloss(half2 uv, half alpha, half4 specColor, TEXTURE2D_ARGS(specGlossMap, sampler_specGlossMap))
{
    half4 specularGloss = half4(0.0h, 0.0h, 0.0h, 1.0h);
#ifdef _SPECGLOSSMAP
    specularGloss = SAMPLE_TEXTURE2D(specGlossMap, sampler_specGlossMap, uv);
#elif defined(_SPECULAR_COLOR)
    specularGloss = specColor;
#endif

#ifdef _GLOSSINESS_FROM_BASE_ALPHA
    specularGloss.a = alpha;
#endif
    return specularGloss;
}

#endif
