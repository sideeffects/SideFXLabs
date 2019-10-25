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
uniform float _posMax;
uniform float _posMin;
uniform int _numOfFrames;
uniform int _pack_normal;
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
TEXTURE2D(_nTex);
SAMPLER(sampler_nTex);
TEXTURE2D(_colorTex);
SAMPLER(sampler_colorTex);
// TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);

struct VATAttributes
{
    float3 positionVAT;
    half3 normalVAT;
    float4 colorVAT;
};

VATAttributes GetAttributesFromTexture(TEXTURE2D_PARAM(_posTex, samplerPosTex),
    TEXTURE2D_PARAM(_posTex2, samplerPosTex2), TEXTURE2D_PARAM(_nTex, samplerNTex), 
    TEXTURE2D_PARAM(_colorTex, samplerColorTex), float4 uv, float4 uv2, float4 vertexCd, 
    float4 vertexPos, float3 vertexN)
{
    VATAttributes output;
    //calculate uv coordinates
    float FPS = 24.0;
    float FPS_div_Frames = FPS / _numOfFrames;
    //Use the line below if you want to use time to animate the object
    float timeInFrames = frac(_speed * _Time.y);
    //The line below is particle age to drive the animation. Comment it out if you want to use time above.
    // timeInFrames = uv.z;

    timeInFrames = ceil(timeInFrames * _numOfFrames);
    timeInFrames /= _numOfFrames;

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
    //get position, normal and colour from textures
    float4 texturePos = SAMPLE_TEXTURE2D_LOD(_posTex, samplerPosTex,
        float2(uv2x, uv2y),0);
    float3 textureN = SAMPLE_TEXTURE2D_LOD(_nTex, samplerNTex,
        float2(uv2x, uv2y),0);
    float4 textureCd = SAMPLE_TEXTURE2D_LOD(_colorTex, samplerColorTex,
        float2(uv2x, uv2y),0);
    if (_doubleTex){
        float3 texturePos2 = SAMPLE_TEXTURE2D_LOD(_posTex2, samplerPosTex2,
        float2(uv2x, uv2y),0);
        texturePos.xyz += (texturePos2 * 0.01);
    }

    //expand normalised position texture values to world space
    float expand = _posMax - _posMin;
    texturePos.xyz *= expand;
    texturePos.xyz += _posMin;
    // texturePos.x *= -1;  //flipped to account for right-handedness of unity
    output.positionVAT = texturePos.xyz;  //swizzle y and z because textures are exported with z-up

    //calculate normal
    //packed normals aren't working and I don't know why
    if (_pack_normal){ 
        //decode float to float2
        float alpha = texturePos.w * 1024;
        // alpha = 0.8286 * 1024;
        float2 f2;
        f2.x = floor(alpha / 32.0) / 31.5;
        f2.y = (alpha - (floor(alpha / 32.0)*32.0)) / 31.5;

        //decode float2 to float3
        half3 f3;
        f2 *= 4;
        f2 -= 2;
        float f2dot = dot(f2,f2);
        // float2 temp = sqrt(1 - (f2dot/4.0)) * f2;
        f3.xy = sqrt(1 - (f2dot/4.0)) * f2;
        // f3.xy = temp;
        f3.z = 1 - (f2dot/2.0);
        f3 = clamp(f3, -1.0, 1.0);
        // f3 = f3.xzy;
        f3.x = 1 - f3.x ;
        output.normalVAT = f3;
        // output.normalVAT = float3(0.0, 1.0, 0.0);
        // float fitTexturePos = (texturePos.w - 0.48) * 4;
        // output.colorVAT = float4(fitTexturePos, 1.0 - fitTexturePos, 0.0, 1.0);
        output.colorVAT = float4(f3.x, 0.0, 0.0, 1.0);
    } else {
        // textureN = textureN.xzy;
        textureN *= 2;
        textureN -= 1;
        // textureN.x *= -1;
        output.normalVAT = textureN;
    }

    //set vertex colour
    output.colorVAT = textureCd;

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
