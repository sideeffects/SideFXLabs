#ifndef LIGHTWEIGHT_SIMPLE_LIT_VAT_FLUID_INPUT_INCLUDED
#define LIGHTWEIGHT_SIMPLE_LIT_VAT_FLUID_INPUT_INCLUDED

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
uniform float _boundingMax;
uniform float _boundingMin;
uniform int _numOfFrames;
uniform float _width;
uniform float _height;
uniform float _speed;

CBUFFER_END

TEXTURE2D(_posTex);
SAMPLER(sampler_posTex);
TEXTURE2D(_nTex);
SAMPLER(sampler_nTex);
TEXTURE2D(_colorTex);
SAMPLER(sampler_colorTex);

struct VATAttributes
{
    float3 positionVAT;
    float3 normalVAT;
    float4 colorVAT;
};

VATAttributes GetAttributesFromTexture(TEXTURE2D_PARAM(_posTex, samplerPosTex), 
    TEXTURE2D_PARAM(_nTex, samplerNTex), TEXTURE2D_PARAM(_colorTex, samplerColorTex), 
    float2 uv, float4 uv2, float4 vertexCd, float4 vertexPos, float3 vertexN)
{
    VATAttributes output;
    //calculate uv coordinates
    float FPS = 24.0;
    float FPS_div_Frames = FPS / _numOfFrames;
    float timeInFrames = frac(FPS_div_Frames * _speed * _Time.y);

    timeInFrames = ceil(timeInFrames * _numOfFrames);
    timeInFrames /= _numOfFrames;

    //get position, normal and colour from textures
    float4 texturePos = SAMPLE_TEXTURE2D_LOD(_posTex, samplerPosTex,
        float2(uv2.x, (1 - timeInFrames) + uv2.y),0);
    float3 textureN = SAMPLE_TEXTURE2D_LOD(_nTex, samplerNTex,
        float2(uv2.x, (1 - timeInFrames) + uv2.y),0);
    float4 textureCd = SAMPLE_TEXTURE2D_LOD(_colorTex, samplerColorTex,
        float2(uv2.x, (1 - timeInFrames) + uv2.y),0);

    //expand normalised position texture values to world space
    float expand = _boundingMax - _boundingMin;
    texturePos.xyz *= expand;
    texturePos.xyz += _boundingMin;
    texturePos.x *= -1;  //flipped to account for right-handedness of unity

    //create camera facing billboard based on uv coordinates
    float3 cameraF = float3(uv.x - 0.5, uv.y - 0.5, 0);
    cameraF *= float3(_width, _height, 1);
    cameraF = mul(cameraF, UNITY_MATRIX_MV);
    output.positionVAT = cameraF + texturePos.xzy;

    //set vertex colour
    output.colorVAT = textureCd;

    output.normalVAT = float3(1.0, 0.0, 0.0);

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

TEXTURE2D(_RampTex);            SAMPLER(sampler_RampTex);

half4 SampleRamp(float lookUpPos, TEXTURE2D_PARAM(RampTex, sampler_RampTex))
{
    half4 rampCd = half4(0.0h, 0.0h, 0.0h, 1.0h);
    rampCd = SAMPLE_TEXTURE2D(RampTex, sampler_RampTex, lookUpPos);

    return rampCd;
}


