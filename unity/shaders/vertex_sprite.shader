Shader "sidefx/vertex_sprite_shader" {
	Properties {
		_Color ("Color", Color) = (1,1,1,1)
		_MainTex ("Albedo (RGB)", 2D) = "white" {}
		_Glossiness ("Smoothness", Range(0,1)) = 0.5
		_Metallic ("Metallic", Range(0,1)) = 0.0
		_boundingMax("Bounding Max", Float) = 1.0
		_boundingMin("Bounding Min", Float) = 1.0
		_numOfFrames("Number Of Frames", int) = 240
		_speed("Speed", Float) = 0.33
		_height("Height", Float) = 1.0
		_width("Width", Float) = 1.0
		[MaterialToggle] _pack_normal ("Pack Normal", Float) = 0
		_posTex ("Position Map (RGB)", 2D) = "white" {}
		_colorTex ("Colour Map (RGB)", 2D) = "white" {}
	}
	SubShader {
		Tags { "Queue"="Transparent" "RenderType"="Opaque" }
		Blend SrcAlpha OneMinusSrcAlpha
		LOD 200
		
		CGPROGRAM
		// Physically based Standard lighting model, and enable shadows on all light types
		#pragma surface surf Standard alpha:fade vertex:vert

		// Use shader model 3.0 target, to get nicer looking lighting
		#pragma target 3.0

		sampler2D _MainTex;
		sampler2D _posTex;
		sampler2D _colorTex;
		uniform float _pack_normal;
		uniform float _boundingMax;
		uniform float _boundingMin;
		uniform float _speed;
		uniform float _height;
		uniform float _width;
		uniform int _numOfFrames;

		struct Input {
			float2 uv_MainTex;
			float4 vcolor : COLOR ;
		};

		half _Glossiness;
		half _Metallic;
		fixed4 _Color;

		// Add instancing support for this shader. You need to check 'Enable Instancing' on materials that use the shader.
		// See https://docs.unity3d.com/Manual/GPUInstancing.html for more information about instancing.
		// #pragma instancing_options assumeuniformscaling
		UNITY_INSTANCING_CBUFFER_START(Props)
			// put more per-instance properties here
		UNITY_INSTANCING_CBUFFER_END

		//vertex function
		void vert(inout appdata_full v){
			//calculate uv coordinates
			float timeInFrames = ((ceil(frac(-_Time.y * _speed) * _numOfFrames))/_numOfFrames) + (1.0/_numOfFrames);

			//get position and colour from textures
			float4 texturePos = tex2Dlod(_posTex,float4(v.texcoord1.x, (timeInFrames + v.texcoord1.y), 0, 0));
			float3 textureCd = tex2Dlod(_colorTex,float4(v.texcoord1.x, (timeInFrames + v.texcoord1.y), 0, 0));

			//expand normalised position texture values to world space
			float expand = _boundingMax - _boundingMin;
			texturePos.xyz *= expand;
			texturePos.xyz += _boundingMin;
			texturePos.x *= -1;  //flipped to account for right-handedness of unity

			//create camera facing billboard based on uv coordinates
			float3 cameraF = float3(v.texcoord.x - 0.5, v.texcoord.y - 0.5, 0);
			cameraF *= float3(_width, _height, 1);
			cameraF = mul(cameraF, UNITY_MATRIX_MV);
			v.vertex.xyz = cameraF;

			v.vertex.xyz += texturePos.xzy;  //swizzle y and z because textures are exported with z-up
			
			//set vertex colour
			v.color.rgb = textureCd;
		}

		void surf (Input IN, inout SurfaceOutputStandard o) {
			// Albedo comes from a texture tinted by color
			fixed4 c = tex2D (_MainTex, IN.uv_MainTex) * _Color;
			o.Albedo = c.rgb * IN.vcolor.rgb; //multiply existing albedo map by vertex colour 
			// Metallic and smoothness come from slider variables
			o.Metallic = _Metallic;
			o.Smoothness = _Glossiness;
			o.Alpha = c.a;
		}
		ENDCG
	}
	FallBack "Diffuse"
}
