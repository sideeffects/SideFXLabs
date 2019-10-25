// Questions: paula@sidefx.com
// Last Update: 05-April-2018

Shader "sidefx/ShaderFunctionsExamples" {
	Properties {
		
		// Multiple Functions Parms
		_ColorTexture("Diffuse Texture", 2D) = "white" {}

		// TextureSheets Parms
		_SmokeColor ("Smoke Color", Color) = (1,1,1,1)
		[Toggle] _UseColorTexture("Use Diffuse Texture", Float) = 0
		_PyroTexture("Pyro Texture", 2D) = "white" {}
		_RampTexture("Ramp Texture", 2D) = "white" {}
		_GradientPower ("Gradient Power", Range(0,2)) = 0.333
		_FireEmissionScale ("Fire Emission Scale", Range(0,30)) = 0.5

		// MotionVector Parms
		[Gamma] _MotionVector("MotionVector Texture", 2D) = "white" {}
		[Toggle] _DoubleMotionVector("Use Double Motion Vector", Float) = 0
		_Rows("Rows", Float) = 8.0
		_Columns("Columns", Float) = 8.0
		_Distortion("Distortion", Range(0, 1)) = 0.041667
	}
	SubShader {
		Tags{ "Queue" = "Transparent" "RenderType" = "Transparent" }
		LOD 200
		
		CGPROGRAM
		#pragma surface surf Standard fullforwardshadows addshadow alpha:fade
		#pragma target 3.0
		#pragma multi_compile_instancing

		sampler2D _PyroTexture;
		sampler2D _RampTexture;
		sampler2D _ColorTexture;
		sampler2D _MotionVector;

		float4 _SmokeColor;

		float _GradientPower;  
		float _FireEmissionScale;
		float _UseColorTexture;
		float _Rows;
		float _Columns;
		float _Distortion;
		float _DoubleMotionVector;

		struct Input {
			float2 uv_PyroTexture;
		};

		float2 GetSubUV(float2 OrigUV, float2 RowCol, float frame) {

			// Calculate Current SubUV
			float SubUVA = frame - frac(frame);
			float2 Scale = float2(1,1) / RowCol;
			float2 SubUV = (float2(fmod(SubUVA, RowCol.r), floor(SubUVA * Scale.r)) + OrigUV) * Scale;
			SubUV.y = 1-SubUV.y; 

			return SubUV; 
		}

		// Function for displacing a texture using a motionvector
		float4 GetMotionVectorDisplacedTexture(float2 f2OrigUV, sampler2D saTexture, sampler2D saMotionVectorTexture, float fDoubleMotionVector, float fCols, float fRows, float fDistortion, float fAnimationPhase ){
		
			// Flipbook Setup
			f2OrigUV.y = 1 - f2OrigUV.y;
			float XColTime = (fCols * fRows) * min(fAnimationPhase, 0.99999);
			float FloorXColTime = floor(XColTime);
			float2 ColRow = float2(fCols, fRows);
			float2 CustomUV = ( float2(FloorXColTime, floor(FloorXColTime/fRows) ) / ColRow) + (f2OrigUV / ColRow);
			CustomUV.y = 1 - CustomUV.y;

			// Blend Phase Between Frames
			float BlendPhase = frac(XColTime.r);
			
			// Offset Frame UVs
			float2 CustomUV2 = (f2OrigUV / ColRow) + float2((FloorXColTime+1.0), floor((FloorXColTime+1.0)/fRows)) / ColRow;
			CustomUV2.y = 1- CustomUV2.y;
			
			// Motion Vector Setup
			float2 PrimMotionVector = tex2D(saMotionVectorTexture, CustomUV).rg;
			PrimMotionVector.g = 1-PrimMotionVector.g;

			float2 PrimMotionVectorBias = PrimMotionVector - 0.5;
			PrimMotionVectorBias *= 2;
			float2 PrimMotionVectorIntens = (PrimMotionVectorBias / ColRow) * fDistortion;

			// Regular Motion Vectors
			float2 PrimMotionVectorAdd = CustomUV + (BlendPhase * PrimMotionVectorIntens);
			float2 PrimMotionVectorSubtract = CustomUV2 - ((1-BlendPhase) * PrimMotionVectorIntens);

			float2 MotionVectorForward = PrimMotionVectorAdd;
			float2 MotionVectorReverse = PrimMotionVectorSubtract;

			// Double Motion Vectors
			if (fDoubleMotionVector) {
				float2 MotionVecForward = tex2D(saMotionVectorTexture, PrimMotionVectorAdd).rg;
				MotionVecForward.g = 1-MotionVecForward.g;
				MotionVecForward -= 0.5;
				MotionVecForward *= 2.0;
				MotionVectorForward = CustomUV + ((fDistortion * ((MotionVecForward -0.5) * 2) / ColRow) * BlendPhase); //DoubleMotionVectorAdd

				float2 MotionVecReverse = tex2D(saMotionVectorTexture, PrimMotionVectorSubtract).rg;
				MotionVecReverse.g = 1-MotionVecReverse.g;
				MotionVecReverse -= 0.5;
				MotionVecReverse *= 2.0;
				
				MotionVectorReverse = CustomUV2 - ((fDistortion * ((MotionVecReverse -0.5) * 2) / ColRow) * (1-BlendPhase)); //DoubleMotionVectorSubtract

			 }

			// Sample Texture with MotionVector Data 
			return lerp(tex2D(saTexture, MotionVectorForward), tex2D(saTexture, MotionVectorReverse), BlendPhase);
		}

		// Function to remap Texturesheets emission data into ramp colorspace
		float3 GetRemappedTextureSheetEmission(sampler2D saRamp, float3 Color, float fGradientPow, float fEmissionScale){

			return tex2D(saRamp, clamp(float2( pow(Color.b, fGradientPow).r, 0.5), 0.05, 0.95)) * fEmissionScale;
		}

		// Function to construct normal vector from TextureSheet Color
		float3 DecodeNormalFromTextureSheet(float3 Color){

			fixed3 Normal;
			Normal.rg = Color.rg * 2 - 1;
			Normal.b = sqrt(1 - (Normal.r*Normal.r - Normal.g*Normal.g));

			return Normal;
		}



		void surf (Input IN, inout SurfaceOutputStandard o) {
			
			
			/* ////////////// MOTION VECTOR EXAMPLE CODE //////////////
			fixed4 c = GetMotionVectorDisplacedTexture(IN.uv_PyroTexture, _ColorTexture, _MotionVector, _DoubleMotionVector, _Columns, _Rows, _Distortion, frac(_Time.y*0.05));

			o.Albedo = c.rgb;
			o.Alpha = c.a;

			*/

			////////////// TEXTURE SHEETS EXAMPLE CODE //////////////
			fixed4 c = tex2D(_PyroTexture, IN.uv_PyroTexture);
			
			// Diffuse
			if (!_UseColorTexture) {
				
				// Use Flat Color for Diffuse
				o.Albedo = _SmokeColor.rgb;

				// Emissive
				fixed3 e = GetRemappedTextureSheetEmission(_RampTexture, c, _GradientPower, _FireEmissionScale);
				o.Albedo += e.rgb;

			} else {

				// Use Color Texture for Diffuse (Multiplied by Tint)
				o.Albedo = tex2D(_ColorTexture, IN.uv_PyroTexture).rgb * _SmokeColor.rgb;
			}

			// Normal
			o.Normal = DecodeNormalFromTextureSheet(c);
			
			// Alpha
			o.Alpha = c.a;
			

		}
		ENDCG
	}
	FallBack "Diffuse"
}
