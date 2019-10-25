//This shader requires Custom Vertex Streams to be turned on in the renderer section of the particle
//Make sure these streams have been added in this specific order:
//Position (POSITION.xyz)
//Normal (NORMAL.xyz)
//Color (COLOR.xyzw)
//UV (TEXCOORD0.xy)
//StableRandom.xy (TEXCOORD0.zw)
//Center (TEXCOORD1.xyz)

Shader "sidefx/Impostor Alpha Blended" {
Properties {
	_TintColor ("Tint Color", Color) = (0.5,0.5,0.5,0.5)
	_MainTex ("Particle Texture", 2D) = "white" {}
	_InvFade ("Soft Particles Factor", Range(0.01,3.0)) = 1.0
	_rows("Rows", Float) = 8.0
	_columns("Columns", Float) = 8.0
	_rotation ("Rotation", Range(0,1)) = 0.0
	[MaterialToggle] _fixed_y ("Fixed Y", Float) = 1
	[MaterialToggle] _animation ("Animation", Float) = 0
	_speed ("Speed", Range(0,10)) = 1.0
	_ImpostorRoundingOffsetX("Impostor Rounding Offset X", Float) = 0.0
	_ImpostorRoundingOffsetY("Impostor Rounding Offset Y", Float) = 0.0
}

Category {
	Tags { "Queue"="Transparent+1" "IgnoreProjector"="True" "RenderType"="Transparent" }
	Blend SrcAlpha OneMinusSrcAlpha
	AlphaTest Greater .01
	ColorMask RGB
	Cull Off Lighting Off ZWrite Off
	BindChannels {
		Bind "Color", color
		Bind "Vertex", vertex
		Bind "TexCoord", texcoord
	}
	
	// ---- Fragment program cards
	SubShader {
		Pass {
		
			CGPROGRAM
			#pragma vertex vert
			#pragma fragment frag
			#pragma fragmentoption ARB_precision_hint_fastest
			#pragma multi_compile_particles
			
			#include "UnityCG.cginc"

			sampler2D _MainTex;
			fixed4 _TintColor;
			uniform float _rows;
			uniform float _columns;
			uniform float _rotation;
			uniform float _fixed_y;
			uniform float _animation;
			uniform float _speed;
			uniform float _ImpostorRoundingOffsetX;
			uniform float _ImpostorRoundingOffsetY;
			
			struct appdata_t {
				float4 vertex : POSITION;
				fixed4 color : COLOR;
				float4 texcoord : TEXCOORD0;
				float4 texcoord1 : TEXCOORD1;
			};

			struct v2f {
				float4 vertex : POSITION;
				fixed4 color : COLOR;
				float2 texcoord : TEXCOORD0;
				#ifdef SOFTPARTICLES_ON
				float4 projPos : TEXCOORD1;
				#endif
			};
			
			float4 _MainTex_ST;

			v2f vert (appdata_t v)
			{
				v2f o;

				//calculate angle in radians from camera to particle
				float3 particleWorldPos = v.texcoord1.xyz;
				float3 lookAt = normalize(_WorldSpaceCameraPos - particleWorldPos);
				float angle = (atan2(lookAt.x, lookAt.z) / 6.283) * -1;

				float radialAngle = frac(_rotation + angle + 0.25);
				
				//slice up the texture coordinates based on the number of rows and columns
				float2 flippedUV = float2(v.texcoord.x, v.texcoord.y);
				float2 uvSlice = flippedUV / float2(_rows, _columns);
				
				//determine which image index in the texture sheet to use
				float frame = _rows * _columns * min(frac(radialAngle), 0.99999);
				frame = floor(frame);

				//use the index to determine the row and column in the texture sheet
				float2 uvShift = float2(frame, floor(frame / _rows))/ float2(_rows, _columns);
				uvShift.y = 1 - uvShift.y;

				float2 uvAnim;
				float2 uvRegion;
				float startOffset = v.texcoord.w;
				//remember to change the render mode to "Vertical Billboard" when using fixed y
				if (_fixed_y) {
					if (_animation) {
						uvAnim.x = floor(radialAngle * _rows)*(1/_rows);
						uvAnim.y = floor((frac(-_Time.y * _speed + startOffset)) * _columns) * (1/_columns);
						uvRegion = uvSlice + uvAnim;
					} else {
						uvRegion = uvSlice + uvShift; 
					}
				//For a full impostor turn off Fixed Y
				} else {
					float upAngle = dot(lookAt,float3(0,1,0));
					float fitUpAngle = (upAngle + 1) * 0.5;
					float likeRoundingX = floor(radialAngle * _rows - _ImpostorRoundingOffsetX)/_rows;
					float likeRoundingY = min(floor(fitUpAngle * _columns - _ImpostorRoundingOffsetY), _columns - 1)/_columns;
					float2 uvOffset = float2(likeRoundingX, likeRoundingY);
					uvRegion = uvSlice + uvOffset;
				}

				o.vertex = UnityObjectToClipPos(v.vertex);
				#ifdef SOFTPARTICLES_ON
				o.projPos = ComputeScreenPos (o.vertex);
				COMPUTE_EYEDEPTH(o.projPos.z);
				#endif
				o.color = v.color;
				o.texcoord = TRANSFORM_TEX(uvRegion,_MainTex);
				return o;
			}

			sampler2D _CameraDepthTexture;
			float _InvFade;
			
			fixed4 frag (v2f i) : COLOR
			{
				#ifdef SOFTPARTICLES_ON
				float sceneZ = LinearEyeDepth (UNITY_SAMPLE_DEPTH(tex2Dproj(_CameraDepthTexture, UNITY_PROJ_COORD(i.projPos))));
				float partZ = i.projPos.z;
				float fade = saturate (_InvFade * (sceneZ-partZ));
				i.color.a *= fade;
				#endif
				
				// i.color.a = tex2D(_MainTex, i.texcoord);
				return 2.0f * i.color * _TintColor * tex2D(_MainTex, i.texcoord);
			}
			ENDCG 
		}
	} 	
	
	// ---- Dual texture cards
	SubShader {
		Pass {
			SetTexture [_MainTex] {
				constantColor [_TintColor]
				combine constant * primary
			}
			SetTexture [_MainTex] {
				combine texture * previous DOUBLE
			}
		}
	}
	
	// ---- Single texture cards (does not do color tint)
	SubShader {
		Pass {
			SetTexture [_MainTex] {
				combine texture * primary
			}
		}
	}
}
}
