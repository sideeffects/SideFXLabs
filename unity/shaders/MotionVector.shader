// Questions: paula@sidefx.com/mikel@sidefx.com
// Last Update: 07-May-2018

Shader "sidefx/MotionVector" {
	Properties {
		
		// Multiple Functions Parms
		_ColorTexture("Diffuse Texture", 2D) = "white" {}

		// TextureSheets Parms
		// _SmokeColor ("Smoke Color", Color) = (1,1,1,1)
		// [Toggle] _UseColorTexture("Use Diffuse Texture", Float) = 0
		// _PyroTexture("Pyro Texture", 2D) = "white" {}
		// _RampTexture("Ramp Texture", 2D) = "white" {}
		//_GradientPower ("Gradient Power", Range(0,2)) = 0.333
		// _FireEmissionScale ("Fire Emission Scale", Range(0,30)) = 0.5

		// MotionVector Parms
		[Gamma] _MotionVector("MotionVector Texture", 2D) = "white" {}
		[Toggle] _DoubleMotionVector("Use Double Motion Vector", Float) = 0
		_Rows("Rows", Float) = 8.0
		_Columns("Columns", Float) = 8.0
		_Distortion("Distortion (1/Sim FPS)", Range(0, 1)) = 0.041667

		// Debug Parms
		//[Toggle] _OverrideTime("Override Time", Float) = 0
		//[Toggle] _OverrideBlend("Override Blend", Float) = 0
		//[Toggle] _OverrideDistort("Override Distort", Float) = 0
		//_TimeOverride ("Time Override", Range(0.001, 0.999)) = 0.001
		//_BlendOverride ("Blend Override", Range(0.001, 0.999)) = 0.001
		//_DistortOverride ("Distort Override", Range(0.001, 0.999)) = 0.001
	}
	SubShader {
		Tags{ "Queue" = "Transparent" "RenderType" = "Transparent" }
		LOD 200
		
		CGPROGRAM
		#pragma surface surf Standard fullforwardshadows addshadow alpha:fade vertex:vert
		#pragma target 3.0
		#pragma multi_compile_instancing

		// sampler2D _PyroTexture;
		// sampler2D _RampTexture;
		sampler2D _ColorTexture;
		sampler2D _MotionVector;

		// float4 _SmokeColor;

		// float _GradientPower;  
		// float _FireEmissionScale;
		// float _UseColorTexture;
		float _Rows;
		float _Columns;
		float _Distortion;
		float _DoubleMotionVector;

		// Debug Controls
		// float _OverrideTime;
		// float _OverrideBlend;
		// float _OverrideDistort;
		// float _TimeOverride;
		// float _BlendOverride;
		// float _DistortOverride;

		struct appdata_particles {
            float4 vertex : POSITION;
            float3 normal : NORMAL;
            float4 color : COLOR;
            float4 texcoords : TEXCOORD0;
            float4 texcoordAge : TEXCOORD1;
            };

        struct Input {
            float2 texcoord;
            float2 texcoord1;
            float age;
            float4 color;
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
			//Debug Override 
			// if (_OverrideTime) {
				// fAnimationPhase = _TimeOverride;
			// }

			// Flipbook Setup
			f2OrigUV.y = 1 - f2OrigUV.y;
			float XColTime = (fCols * fRows) * min(fAnimationPhase, 0.99999);
			float FloorXColTime = floor(XColTime);
			float2 ColRow = float2(fCols, fRows);
			float2 CustomUV = ( float2(FloorXColTime, floor(FloorXColTime/fRows) ) / ColRow) + (f2OrigUV / ColRow);
			CustomUV.y = 1 - CustomUV.y;

			// Blend Phase Between Frames
			float BlendPhase = frac(XColTime.r);

			// Debug Override
			// if (_OverrideBlend) {
				// BlendPhase = _BlendOverride;
			// }

			float mvDistort = BlendPhase;

			// Debug Override
			// if (_OverrideDistort) {
				// mvDistort = _DistortOverride;
			// }
			
			// Offset Frame UVs
			float2 CustomUV2 = (f2OrigUV / ColRow) + float2((FloorXColTime+1.0), floor((FloorXColTime+1.0)/fRows)) / ColRow;
			CustomUV2.y = 1- CustomUV2.y;
			
			// Motion Vector Setup
			float2 PrimMotionVector = tex2D(saMotionVectorTexture, CustomUV).rg;
			PrimMotionVector.g = 1-PrimMotionVector.g;

			// float2 PrimMotionVectorBias = (PrimMotionVector - 0.5) * 2.0;
			float2 PrimMotionVectorBias = PrimMotionVector - 0.5;
			PrimMotionVectorBias *= 2;
			// float PrimMotionVectorBias = PrimMotionVector;
			float2 PrimMotionVectorIntens = (PrimMotionVectorBias / ColRow) * fDistortion;

			// Regular Motion Vectors
			float2 PrimMotionVectorAdd = CustomUV + (mvDistort * PrimMotionVectorIntens);
			float2 PrimMotionVectorSubtract = CustomUV2 - ((1-mvDistort) * PrimMotionVectorIntens);

			float2 MotionVectorForward = PrimMotionVectorAdd;
			float2 MotionVectorReverse = PrimMotionVectorSubtract;

			// Double Motion Vectors
			if (fDoubleMotionVector) {
				// PrimMotionVectorAdd.g = 1 - PrimMotionVectorAdd.g;
				float2 MotionVecForward = tex2D(saMotionVectorTexture, PrimMotionVectorAdd).rg;
				MotionVecForward.g = 1-MotionVecForward.g;
				MotionVecForward -= 0.5;
				MotionVecForward *= 2.0;
				MotionVectorForward = CustomUV + ((fDistortion * MotionVecForward / ColRow) * mvDistort); //DoubleMotionVectorAdd

				// PrimMotionVectorSubtract.g = 1 - PrimMotionVectorSubtract.g;
				float2 MotionVecReverse = tex2D(saMotionVectorTexture, PrimMotionVectorSubtract).rg;
				MotionVecReverse.g = 1-MotionVecReverse.g;
				MotionVecReverse -= 0.5;
				MotionVecReverse *= 2.0;


				MotionVectorReverse = CustomUV2 - ((fDistortion * MotionVecReverse / ColRow) * (1-mvDistort)); //DoubleMotionVectorSubtract

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

		void vert(inout appdata_particles v, out Input o) {
            UNITY_INITIALIZE_OUTPUT(Input,o);
            o.texcoord = v.texcoords.xy;
            o.texcoord1 = v.texcoords.zw;
            o.age = v.texcoordAge.x;
            o.color = v.color;
        }	

		void surf (Input IN, inout SurfaceOutputStandard o) {
			
			
			////////////// MOTION VECTOR EXAMPLE CODE //////////////
			fixed4 c = GetMotionVectorDisplacedTexture(IN.texcoord, _ColorTexture, 
				_MotionVector, _DoubleMotionVector, _Columns, _Rows, _Distortion, IN.age);

			o.Albedo = c.rgb;
			o.Alpha = c.a;

			

			/* ////////////// TEXTURE SHEETS EXAMPLE CODE //////////////
			fixed4 c = tex2D(_PyroTexture, IN.texcoord);
			
			// Diffuse
			if (!_UseColorTexture) {
				
				// Use Flat Color for Diffuse
				o.Albedo = _SmokeColor.rgb;

				// Emissive
				fixed3 e = GetRemappedTextureSheetEmission(_RampTexture, c, _GradientPower, _FireEmissionScale);
				o.Albedo += e.rgb;

			} else {

				// Use Color Texture for Diffuse (Multiplied by Tint)
				o.Albedo = tex2D(_ColorTexture, IN.texcoord).rgb * _SmokeColor.rgb;
			}

			// Normal
			o.Normal = DecodeNormalFromTextureSheet(c);
			
			// Alpha
			o.Alpha = c.a;
			*/

		}
		ENDCG
	}
	FallBack "Diffuse"
}
