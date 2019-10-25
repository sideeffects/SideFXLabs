#ifndef LIGHTWEIGHT_SIMPLE_LIT_VAT_INPUT_INCLUDED
#define LIGHTWEIGHT_SIMPLE_LIT_VAT_INPUT_INCLUDED

#include "Packages/com.unity.render-pipelines.lightweight/ShaderLibrary/Core.hlsl"
#include "Packages/com.unity.render-pipelines.lightweight/ShaderLibrary/SurfaceInput.hlsl"

CBUFFER_START(UnityPerMaterial)
float4 _BaseMap_ST;
half4 _BaseColor;
half4 _SpecColor;
half4 _EmissionColor;
half _Cutoff;
half _Shininess;

//--------------------------------------
// Declare shader properties
uniform float _pivMax;
uniform float _pivMin;
uniform float _posMax;
uniform float _posMin;
uniform int _numOfFrames;
uniform float _speed;
uniform int _doubleTex;
uniform int _padPowTwo;
uniform float _textureSizeX;
uniform float _textureSizeY;
uniform float _paddedSizeX;
uniform float _paddedSizeY;
CBUFFER_END

TEXTURE2D(_posTex);
SAMPLER(sampler_posTex);
TEXTURE2D(_posTex2);
SAMPLER(sampler_posTex2);
TEXTURE2D(_rotTex);
SAMPLER(sampler_rotTex);

struct VATAttributes
{
    float3 positionVAT;
    float3 normalVAT;
};

VATAttributes GetAttributesFromTexture(TEXTURE2D_PARAM(_posTex, samplerPosTex),
    TEXTURE2D_PARAM(_posTex2, samplerPosTex2), TEXTURE2D_PARAM(_rotTex, samplerRotTex), 
    float4 uv, float4 uv2, float4 vertexCd, float4 vertexPos, float3 vertexN)
{
    VATAttributes output;
    float FPS = 24.0;
    float FPS_div_Frames = FPS / _numOfFrames;
    //Use the line below if you want to use time to animate the object
    float timeInFrames = frac(_speed * _Time.y);
    //The line below is particle age to drive the animation. Comment it out if you want to use time above.
    // timeInFrames = uv.z;

    timeInFrames = ceil(timeInFrames * _numOfFrames);
    timeInFrames /= _numOfFrames;
    timeInFrames += (1/_numOfFrames);

    float x_ratio = _textureSizeX/_paddedSizeX;
    float y_ratio = _textureSizeY/_paddedSizeY;
    float uv2y = 0;
    float uv2x = 0;
    if (_padPowTwo) {
        uv2x = uv2.x * x_ratio;
        uv2y = (1 - (timeInFrames * y_ratio)) + (1 - ((1 - uv2.y) * y_ratio));
    }
    else {
        uv2y = (1 - timeInFrames) + uv2.y;
        uv2x = uv2.x;
    }

    //get position and rotation(quaternion) from textures
    float4 texturePos = SAMPLE_TEXTURE2D_LOD(_posTex, samplerPosTex,
        float2(uv2x, uv2y),0);
    float4 textureRot = (SAMPLE_TEXTURE2D_LOD(_rotTex, samplerRotTex, 
        float2(uv2x, uv2y),0));
    if (_doubleTex){
        float3 texturePos2 = SAMPLE_TEXTURE2D_LOD(_posTex2, samplerPosTex2,
        float2(uv2x, uv2y),0);
        texturePos.xyz += (texturePos2 * 0.01);
    }

    //expand normalised position texture values to world space
    float expand1 = _posMax - _posMin;
    texturePos.xyz *= expand1;
    texturePos.xyz += _posMin;
    // texturePos.x *= -1;  //flipped to account for right-handedness of unity
    // texturePos.xyz = texturePos.xzy;  //swizzle y and z because textures are exported with z-up

    //expand normalised pivot vertex colour values to world space
    float expand = _pivMax - _pivMin;
    float3 pivot = vertexCd.rgb;
    pivot.xyz *= expand;
    pivot.xyz += _pivMin;
    // pivot.x *=  -1;
    // pivot = pivot.xzy;
    float3 atOrigin = vertexPos.xyz - pivot;

    //calculate rotation
    textureRot *= 2.0;
    textureRot -= 1.0;
    float4 quat = 0;

    //swizzle and flip quaternion from ue4 to unity
    // quat.x = textureRot.x;
    // quat.y = -textureRot.y;
    // quat.z = -textureRot.z;
    // quat.w = textureRot.w;
    quat = textureRot;

    float3 rotated = atOrigin + 2.0 * cross(quat.xyz, cross(quat.xyz, atOrigin) + quat.w * atOrigin);

    output.positionVAT = rotated;
    // output.positionVAT = atOrigin;
    output.positionVAT += pivot;
    output.positionVAT += texturePos;
    // output.positionVAT += center;

    //calculate normal
    float3 rotatedNormal = vertexN + 2.0 * cross(quat.xyz, cross(quat.xyz, vertexN) + quat.w * vertexN);
    output.normalVAT = rotatedNormal;

    return output;

}

TEXTURE2D(_SpecGlossMap);       SAMPLER(sampler_SpecGlossMap);

half4 SampleSpecularSmoothness(half2 uv, half alpha, half4 specColor, TEXTURE2D_PARAM(specMap, sampler_specMap))
{
    half4 specularSmoothness = half4(0.0h, 0.0h, 0.0h, 1.0h);
#ifdef _SPECGLOSSMAP
    specularSmoothness = SAMPLE_TEXTURE2D(specMap, sampler_specMap, uv) * specColor;
#elif defined(_SPECULAR_COLOR)
    specularSmoothness = specColor;
#endif

#ifdef _GLOSSINESS_FROM_BASE_ALPHA
    specularSmoothness.a = exp2(10 * alpha + 1);
#else
    specularSmoothness.a = exp2(10 * specularSmoothness.a + 1);
#endif

    return specularSmoothness;
}

#endif
