// Questions: paula@sidefx.com/mikel@sidefx.com
// Last Update: 07-May-2018

Shader "sidefx/PyroTextureSheet" {
	Properties {
		// TextureSheets Parms
		_SmokeColor ("Smoke Color", Color) = (1,1,1,1)
		_GradientPower ("Gradient Power", Range(0,2)) = 0.333
		_FireEmissionScale ("Fire Emission Scale", Range(0,30)) = 0.5
		_PyroTexture("Pyro Texture", 2D) = "white" {}
		_RampTexture("Ramp Texture", 2D) = "white" {}

		// Multiple Functions Parms
		[Toggle] _UseColorTexture("Use Diffuse Texture", Float) = 0
		_ColorTexture("Diffuse Texture", 2D) = "white" {}

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

		float4 _SmokeColor;

		float _GradientPower;  
		float _FireEmissionScale;
		float _UseColorTexture;

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
