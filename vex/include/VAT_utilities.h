function vector coord_swizzle_vector(vector coord; int coord_swizzle, coord_flip, inv;)
{
        vector result;
        vector swizzle;
        if (coord_swizzle == 0) swizzle = set(0, 1, 2);
        else if (coord_swizzle == 1) swizzle = set(0, 2, 1);
        else if (coord_swizzle == 2) swizzle = set(1, 0, 2);
        else if (coord_swizzle == 3) swizzle = set(1, 2, 0);
        else if (coord_swizzle == 4) swizzle = set(2, 0, 1);
        else if (coord_swizzle == 5) swizzle = set(2, 1, 0);
        
        vector flip;
        if (coord_flip == 0) flip = set(1,1,1);
        else if (coord_flip == 1) flip = set(-1,1,1);
        else if (coord_flip == 2) flip = set(1,-1,1);
        else if (coord_flip == 3) flip = set(1,1,-1);
        else if (coord_flip == 4) flip = set(-1,-1,1);
        else if (coord_flip == 5) flip = set(-1,1,-1);
        else if (coord_flip == 6) flip = set(-1,-1,-1);
        else if (coord_flip == 7) flip = set(1,-1,-1);
        
        result = swizzle(coord, swizzle.x, swizzle.y, swizzle.z) * flip;

        return result;
}

function vector4 coord_swizzle_vector(vector4 coord; int coord_swizzle, coord_flip, inv;)
{
        vector4 result;
        vector swizzle;
        if (coord_swizzle == 0) swizzle = set(0, 1, 2);
        else if (coord_swizzle == 1) swizzle = set(0, 2, 1);
        else if (coord_swizzle == 2) swizzle = set(1, 0, 2);
        else if (coord_swizzle == 3) swizzle = set(1, 2, 0);
        else if (coord_swizzle == 4) swizzle = set(2, 0, 1);
        else if (coord_swizzle == 5) swizzle = set(2, 1, 0);
        
        vector flip;
        if (coord_flip == 0) flip = set(1,1,1);
        else if (coord_flip == 1) flip = set(-1,1,1);
        else if (coord_flip == 2) flip = set(1,-1,1);
        else if (coord_flip == 3) flip = set(1,1,-1);
        else if (coord_flip == 4) flip = set(-1,-1,1);
        else if (coord_flip == 5) flip = set(-1,1,-1);
        else if (coord_flip == 6) flip = set(-1,-1,-1);
        else if (coord_flip == 7) flip = set(1,-1,-1);
        
        result = swizzle(coord, swizzle.x, swizzle.y, swizzle.z) * flip;
        result.z = coord.z;

        return result;
}

function vector4 coord_swizzle_quaternion(vector4 src; int quaternion_flip;)
{
    vector4 result;
    vector4 flip;
    if (quaternion_flip == 0) flip = set(1,1,1,1);
    else if (quaternion_flip == 1) flip = set(-1,1,1,1);
    else if (quaternion_flip == 2) flip = set(1,-1,1,1);
    else if (quaternion_flip == 3) flip = set(1,1,-1,1);
    else if (quaternion_flip == 4) flip = set(1,1,1,-1);
    else if (quaternion_flip == 5) flip = set(-1,-1,1,1);
    else if (quaternion_flip == 6) flip = set(-1,1,-1,1);
    else if (quaternion_flip == 7) flip = set(-1,1,1,-1);
    else if (quaternion_flip == 8) flip = set(-1,-1,-1,1);
    else if (quaternion_flip == 9) flip = set(-1,-1,1,-1);
    else if (quaternion_flip == 10) flip = set(-1,-1,-1,-1);
    else if (quaternion_flip == 11) flip = set(1,-1,-1,1);
    else if (quaternion_flip == 12) flip = set(1,1,-1,-1);
    else if (quaternion_flip == 13) flip = set(1,-1,-1,-1);
    else if (quaternion_flip == 14) flip = set(1,1,-1,-1);
    
    result = src * flip;
    
    return result;
}