float3 VAT_unpackAlpha(float alpha)
{
    //decode float to float2
    alpha *= 1024;
    // alpha = 0.8286 * 1024;
    float2 f2;
    f2.x = floor(alpha / 32.0) / 31.5;
    f2.y = (alpha - (floor(alpha / 32.0)*32.0)) / 31.5;

    //decode float2 to float3
    float3 f3;
    f2 *= 4;
    f2 -= 2;
    float f2dot = dot(f2,f2);
    f3.xy = sqrt(1 - (f2dot/4.0)) * f2;
    f3.z = 1 - (f2dot/2.0);
    f3 = clamp(f3, -1.0, 1.0);
    return f3;    
}

float2 VAT_uvPosition(float2 uvIndex, int numOfFrames, float speed, float time, float2 paddedRatio)
{
    float2 uvPosition;
    float FPS = 24.0;
    float FPS_div_Frames = FPS / numOfFrames;
    float timeInFrames = frac(speed * time);

    timeInFrames = ceil(timeInFrames * numOfFrames);
    timeInFrames /= numOfFrames;
    timeInFrames += (1/numOfFrames);

    uvPosition.x = uvIndex.x * paddedRatio.x;
    uvPosition.y = (1 - (timeInFrames * paddedRatio.y)) + (1 - ((1 - uvIndex.y) * paddedRatio.y));

    return uvPosition;
}
// Rigid VAT
void VAT_Rigid_float(
    float3 restPosition,
    float3 restNormal,
    float3 vertexColor,
    float2 uvIndex,
    SamplerState texSampler,
    Texture2D positionMap,
    Texture2D rotationMap,
    float2 positionBounds,
    float2 pivotBounds,
    float time,
    float speed,
    int numOfFrames,
    float2 paddedRatio,
    out float3 outPosition,
    out float3 outNormal
)
{
    float2 uvPosition = VAT_uvPosition(uvIndex, numOfFrames, speed, time, paddedRatio);

    float4 texturePos = positionMap.SampleLevel(texSampler, uvPosition, 0);
    float4 textureRot = rotationMap.SampleLevel(texSampler, uvPosition, 0);

    texturePos.xyz = lerp(positionBounds.x, positionBounds.y, texturePos.xyz);

    float3 pivot = lerp(pivotBounds.x, pivotBounds.y, vertexColor.xyz);

    float3 atOrigin = restPosition - pivot;

    //calculate rotation
    textureRot *= 2.0;
    textureRot -= 1.0;
    float4 quat = 0;

    quat = textureRot;

    float3 rotated = 2.0 * cross(quat.xyz, cross(quat.xyz, atOrigin) + quat.w * atOrigin);
    float3 rotatedNormal = restNormal + 2.0 * cross(quat.xyz, cross(quat.xyz, restNormal) + quat.w * restNormal);

    outPosition = atOrigin + rotated + texturePos;
    outNormal = rotatedNormal;
}

// Soft VAT
void VAT_Soft_float(
    float3 restPosition,
    float2 uvIndex,
    SamplerState texSampler,
    Texture2D positionMap,
    Texture2D normalMap,
    Texture2D colorMap,
    float2 positionBounds,
    float time,
    float speed,
    int numOfFrames,
    float2 paddedRatio,
    bool packNorm,
    out float3 outPosition,
    out float3 outNormal,
    out float3 outColor
)
{
    float2 uvPosition = VAT_uvPosition(uvIndex, numOfFrames, speed, time, paddedRatio);

    float4 texturePos = positionMap.SampleLevel(texSampler, uvPosition, 0);
    float4 textureN = normalMap.SampleLevel(texSampler, uvPosition, 0);
    float4 textureCd = colorMap.SampleLevel(texSampler, uvPosition, 0);

    texturePos.xyz = lerp(positionBounds.x, positionBounds.y, texturePos.xyz);

    //calculate normal
    if (packNorm){
        outNormal = VAT_unpackAlpha(texturePos.w);
    } else {
        outNormal = textureN * 2 - 1;
    }

    outPosition = restPosition + texturePos;
    outColor = textureCd.xyz;
}

// Fluid VAT
void VAT_Fluid_float(
    float2 uvIndex,
    SamplerState texSampler,
    Texture2D positionMap,
    Texture2D normalMap,
    Texture2D colorMap,
    float2 positionBounds,
    float time,
    float speed,
    int numOfFrames,
    float2 paddedRatio,
    bool packNorm,
    out float3 outPosition,
    out float3 outNormal,
    out float3 outColor
)
{
    float2 uvPosition = VAT_uvPosition(uvIndex, numOfFrames, speed, time, paddedRatio);

    float4 texturePos = positionMap.SampleLevel(texSampler, uvPosition, 0);
    float4 textureN = normalMap.SampleLevel(texSampler, uvPosition, 0);
    float4 textureCd = colorMap.SampleLevel(texSampler, uvPosition, 0);

    texturePos.xyz = lerp(positionBounds.x, positionBounds.y, texturePos.xyz);

    //calculate normal
    if (packNorm){
        outNormal = VAT_unpackAlpha(texturePos.w);
    } else {
        outNormal = textureN * 2 - 1;
    }

    outPosition = texturePos;
    outColor = textureCd.xyz;
}

// Sprite VAT
void VAT_Sprite_float(
    float2 uvIndex,
    float2 uv,
    SamplerState texSampler,
    Texture2D positionMap,
    Texture2D colorMap,
    float2 positionBounds,
    float2 widthHeight,
    float time,
    float speed,
    int numOfFrames,
    float2 paddedRatio,
    bool packNorm,
    matrix MV,
    out float3 outPosition,
    out float3 outNormal,
    out float3 outColor
)
{
    float2 uvPosition = VAT_uvPosition(uvIndex, numOfFrames, speed, time, paddedRatio);

    float4 texturePos = positionMap.SampleLevel(texSampler, uvPosition, 0);
    float4 textureCd = colorMap.SampleLevel(texSampler, uvPosition, 0);

    texturePos.xyz = lerp(positionBounds.x, positionBounds.y, texturePos.xyz);

    outNormal = float3(1.0, 0.0, 0.0);

    //create camera facing billboard based on uv coordinates
    float3 cameraF = float3(0.5 - uv.x, uv.y - 0.5, 0);
    cameraF *= float3(widthHeight.x, widthHeight.y, 1);
    cameraF = mul(cameraF, MV);

    outPosition = cameraF + texturePos.xyz;
    outColor = textureCd.xyz;
}