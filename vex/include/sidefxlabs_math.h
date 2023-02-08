#ifndef __sidefxlabs_math_h__
#define __sidefxlabs_math_h__


#define LABS_2PI     6.28318530718
#define LABS_RAD360  6.28318530718
#define LABS_PI      3.14159265359
#define LABS_RAD180  3.14159265359
#define LABS_PI2     1.57079632679
#define LABS_RAD90   1.57079632679

#define LABS_E       2.71828182846
#define LABS_SR2     1.41421356237

// Defines 32-bit tolerances
#define LABS_TOL16    0.000001 // Accurate below 16
#define LABS_TOL128   0.00001  // Accurate below 128
#define LABS_TOL1K    0.0001   // Accurate below 1024
#define LABS_TOL      0.0001   // Accurate below 1024 (default tolerance)
#define LABS_TOL16K   0.001    // Accurate below 16384
#define LABS_TOL130K  0.01     // Accurate below 131072
#define LABS_TOL1M    0.1      // Accurate below 1048576


// Triangle Area

float labs_triarea(const vector pos_a, pos_b, pos_c)
{
    return 0.5 * length(cross(pos_a - pos_c, pos_b - pos_c));
}

float labs_triarea(const int geometry, ptnum_a, ptnum_b, ptnum_c)
{
    return labs_triarea(vector(point(geometry, "P", ptnum_a)),
                        vector(point(geometry, "P", ptnum_b)),
                        vector(point(geometry, "P", ptnum_c)));
}

float labs_triarea(const int geometry, primnum)
{
    return labs_triarea(geometry,
                        primpoint(geometry, primnum, 0),
                        primpoint(geometry, primnum, 1),
                        primpoint(geometry, primnum, 2));
}


// Plane Normal

vector labs_planenormal(const vector pos_a, pos_b, pos_c; const int normalized)
{
    // Uses left-hand rule (Houdini's default face winding order).
    // If not normalized, the magnitude of the output vector is
    // the area of the input triangle.
    return normalized ?
           normalize(cross(pos_b - pos_c, pos_a - pos_c)) :
           0.5 * cross(pos_b - pos_c, pos_a - pos_c);
}

vector labs_planenormal(const int geometry, ptnum_a, ptnum_b, ptnum_c, normalized)
{
    return labs_planenormal(vector(point(geometry, "P", ptnum_a)),
                            vector(point(geometry, "P", ptnum_b)),
                            vector(point(geometry, "P", ptnum_c)), normalized);
}

vector labs_planenormal(const int geometry, primnum, normalized)
{
    return labs_planenormal(geometry,
                            primpoint(geometry, primnum, 0),
                            primpoint(geometry, primnum, 1),
                            primpoint(geometry, primnum, 2), normalized);
}


// Is to the Right Of

int labs_istotheright(const vector pivot, forward, up, pos)
{
    return (int)sign(dot(cross(pos - pivot, forward), up));
}


// Is Above

int labs_isabove(const vector plane_pos, plane_normal, pos)
{
    return (int)sign(dot(pos - plane_pos, plane_normal));
}

int labs_isabove(const vector pos_a, pos_b, pos_c, pos)
{
    // Uses left-hand rule (Houdini's default face winding order)
    return (int)sign(dot(cross(pos - pos_a, pos_c - pos_a), pos_b - pos_a));
}

int labs_isabove(const int geometry, ptnum_a, ptnum_b, ptnum_c; const vector pos)
{
    return labs_isabove(vector(point(geometry, "P", ptnum_a)),
                        vector(point(geometry, "P", ptnum_b)),
                        vector(point(geometry, "P", ptnum_c)), pos);
}

int labs_isabove(const int geometry, primnum; const vector pos)
{
    return labs_isabove(geometry,
                        primpoint(geometry, primnum, 0),
                        primpoint(geometry, primnum, 1),
                        primpoint(geometry, primnum, 2), pos);
}


// Point-Plane Distance

float labs_pointplanedist(const vector plane_pos, plane_unit_normal, pos)
{
    return dot(pos - plane_pos, plane_unit_normal);
}

float labs_pointplanedist(const vector pos_a, pos_b, pos_c, pos)
{
    return labs_pointplanedist(pos_a, labs_planenormal(pos_a, pos_b, pos_c, 1), pos);
}

float labs_pointplanedist(const int geometry, ptnum_a, ptnum_b, ptnum_c; const vector pos)
{
    return labs_pointplanedist(vector(point(geometry, "P", ptnum_a)),
                               vector(point(geometry, "P", ptnum_b)),
                               vector(point(geometry, "P", ptnum_c)), pos);
}

float labs_pointplanedist(const int geometry, primnum; const vector pos)
{
    return labs_pointplanedist(geometry,
                               primpoint(geometry, primnum, 0),
                               primpoint(geometry, primnum, 1),
                               primpoint(geometry, primnum, 2), pos);
}


// Point-Plane Projection

float labs_pointplaneproj(const vector plane_pos, plane_unit_normal, pos; export vector nearest_pos)
{
    float signed_dist = dot(pos - plane_pos, plane_unit_normal);
    nearest_pos = pos - signed_dist * plane_unit_normal;
    return signed_dist;
}

float labs_pointplaneproj(const vector pos_a, pos_b, pos_c, pos; export vector nearest_pos)
{
    return labs_pointplaneproj(pos_a, labs_planenormal(pos_a, pos_b, pos_c, 1), pos, nearest_pos);
}

float labs_pointplaneproj(const int geometry, ptnum_a, ptnum_b, ptnum_c; const vector pos; export vector nearest_pos)
{
    return labs_pointplaneproj(vector(point(geometry, "P", ptnum_a)),
                               vector(point(geometry, "P", ptnum_b)),
                               vector(point(geometry, "P", ptnum_c)), pos, nearest_pos);
}

float labs_pointplaneproj(const int geometry, primnum; const vector pos; export vector nearest_pos)
{
    return labs_pointplaneproj(geometry,
                               primpoint(geometry, primnum, 0),
                               primpoint(geometry, primnum, 1),
                               primpoint(geometry, primnum, 2), pos, nearest_pos);
}


// Point-Line Distance

float labs_pointlinedist(const vector line_pos, line_unit_direction, pos)
{
    // This outperforms the cross product (triangle area) approach in accuracy
    return distance(pos, line_pos + dot(pos - line_pos, line_unit_direction) * line_unit_direction);
}

float labs_pointlinedist(const int geometry, ptnum_a, ptnum_b; const vector pos)
{
    vector line_pos = point(geometry, "P", ptnum_a);
    return labs_pointlinedist(line_pos, normalize(vector(point(geometry, "P", ptnum_b)) - line_pos), pos);
}

float labs_pointlinedist(const int geometry, primnum; const vector pos)
{
    return labs_pointlinedist(geometry,
                              primpoint(geometry, primnum, 0),
                              primpoint(geometry, primnum, 1), pos);
}


// Point-Line Projection

float labs_pointlineproj(const vector line_pos, line_unit_direction, pos; export vector nearest_pos)
{
    nearest_pos = line_pos + dot(pos - line_pos, line_unit_direction) * line_unit_direction;
    return distance(pos, nearest_pos);
}

float labs_pointlineproj(const int geometry, ptnum_a, ptnum_b; const vector pos; export vector nearest_pos)
{
    vector line_pos = point(geometry, "P", ptnum_a);
    return labs_pointlineproj(line_pos, normalize(vector(point(geometry, "P", ptnum_b)) - line_pos), pos, nearest_pos);
}

float labs_pointlineproj(const int geometry, primnum; const vector pos; export vector nearest_pos)
{
    return labs_pointlineproj(geometry,
                              primpoint(geometry, primnum, 0),
                              primpoint(geometry, primnum, 1), pos, nearest_pos);
}


// Point-Segment Distance

float labs_pointsegmentdist(const vector pos_a, pos_b, pos)
{
    vector vec_ab = pos_b - pos_a;

    if (dot(pos - pos_a, vec_ab) <= 0)
        return distance(pos, pos_a);
    else if (dot(pos - pos_b, vec_ab) >= 0)
        return distance(pos, pos_b);
    else
        return labs_pointlinedist(pos_a, normalize(vec_ab), pos);
}

float labs_pointsegmentdist(const int geometry, ptnum_a, ptnum_b; const vector pos)
{
    return labs_pointsegmentdist(vector(point(geometry, "P", ptnum_a)),
                                 vector(point(geometry, "P", ptnum_b)), pos);
}

float labs_pointsegmentdist(const int geometry, primnum; const vector pos)
{
    return labs_pointsegmentdist(geometry,
                                 primpoint(geometry, primnum, 0),
                                 primpoint(geometry, primnum, 1), pos);
}


// Point-Segment Projection

float labs_pointsegmentproj(const vector pos_a, pos_b, pos; export vector nearest_pos)
{
    vector vec_ab = pos_b - pos_a;

    if (dot(pos - pos_a, vec_ab) <= 0)
    {
        nearest_pos = pos_a;
        return distance(pos, nearest_pos);
    }
    else if (dot(pos - pos_b, vec_ab) >= 0)
    {
        nearest_pos = pos_b;
        return distance(pos, nearest_pos);
    }
    else
    {
        return labs_pointlineproj(pos_a, normalize(vec_ab), pos, nearest_pos);
    }
}

float labs_pointsegmentproj(const int geometry, ptnum_a, ptnum_b; const vector pos; export vector nearest_pos)
{
    return labs_pointsegmentproj(vector(point(geometry, "P", ptnum_a)),
                                 vector(point(geometry, "P", ptnum_b)), pos, nearest_pos);
}

float labs_pointsegmentproj(const int geometry, primnum; const vector pos; export vector nearest_pos)
{
    return labs_pointsegmentproj(geometry,
                                 primpoint(geometry, primnum, 0),
                                 primpoint(geometry, primnum, 1), pos, nearest_pos);
}


// Is Outside Triangle

int labs_isoutsidetri(const vector pos_a, pos_b, pos_c, coplanar_pos)
{
    vector vec_a = pos_a - coplanar_pos;
    vector vec_b = pos_b - coplanar_pos;
    vector vec_c = pos_c - coplanar_pos;
    vector cross_ab = cross(vec_a, vec_b);
    vector cross_bc = cross(vec_b, vec_c);
    float dot_abbc = dot(cross_ab, cross_bc);

    if (dot_abbc < 0)
    {
        return 1;
    }
    else
    {
        vector cross_ca = cross(vec_c, vec_a);
        float dot_bcca = dot(cross_bc, cross_ca);

        if (dot_bcca < 0)
        {
            return 1;
        }
        else
        {
            float dot_caab = dot(cross_ca, cross_ab);

            if (dot_caab < 0)
                return 1;
            else if (dot_abbc * dot_bcca * dot_caab == 0)
                return 0;
            else
                return -1;
        }
    }
}

int labs_isoutsidetri(const int geometry, ptnum_a, ptnum_b, ptnum_c; const vector coplanar_pos)
{
    return labs_isoutsidetri(vector(point(geometry, "P", ptnum_a)),
                             vector(point(geometry, "P", ptnum_b)),
                             vector(point(geometry, "P", ptnum_c)), coplanar_pos);
}

int labs_isoutsidetri(const int geometry, primnum; const vector coplanar_pos)
{
    return labs_isoutsidetri(geometry,
                             primpoint(geometry, primnum, 0),
                             primpoint(geometry, primnum, 1),
                             primpoint(geometry, primnum, 2), coplanar_pos);
}


// Point-Triangle-Edge Distance

float labs_pointtriedgedist(const vector pos_a, pos_b, pos_c, coplanar_pos)
{
    vector vec_ab = pos_b - pos_a;
    vector vec_bc = pos_c - pos_b;
    vector normal = cross(vec_ab, vec_bc);
    vector vec_ap = coplanar_pos - pos_a;
    vector vec_bp = coplanar_pos - pos_b;
    float dot_an = dot(cross(vec_ab, vec_ap), normal);

    if (dot_an <= 0)  // Outside of or on line AB:
    {
        if (dot(vec_ap, vec_ab) <= 0)  // Behind AB:
        {
            vector vec_ca = pos_a - pos_c;

            if (dot(vec_ap, vec_ca) >= 0)  // In front of CA:
            {
                return distance(coplanar_pos, pos_a);
            }
            else  // Between C and A (overlapping zone):
            {
                vector vec_ca_norm = normalize(vec_ca);
                return distance(coplanar_pos, pos_c + max(0, dot(coplanar_pos - pos_c, vec_ca_norm)) * vec_ca_norm);
            }
        }
        else if (dot(vec_bp, vec_ab) >= 0)  // In front of AB:
        {
            if (dot(vec_bp, vec_bc) <= 0)  // Behind BC:
            {
                return distance(coplanar_pos, pos_b);
            }
            else  // Between B and C (overlapping zone):
            {
                vector vec_bc_norm = normalize(vec_bc);
                return distance(coplanar_pos, pos_b + min(length(vec_bc), dot(vec_bp, vec_bc_norm)) * vec_bc_norm);
            }
        }
        else  // Between A and B:
        {
            vector vec_ab_norm = normalize(vec_ab);
            return distance(coplanar_pos, pos_a + dot(vec_ap, vec_ab_norm) * vec_ab_norm);
        }
    }
    else
    {
        float dot_bn = dot(cross(vec_bc, vec_bp), normal);
        vector vec_cp = coplanar_pos - pos_c;

        if (dot_bn <= 0)  // Outside of or on line BC:
        {
            if (dot(vec_bp, vec_bc) <= 0)  // Behind BC:
            {
                return distance(coplanar_pos, pos_b);
            }
            else if (dot(vec_cp, vec_bc) >= 0)  // In front of BC:
            {
                vector vec_ca = pos_a - pos_c;

                if (dot(vec_cp, vec_ca) <= 0)  // Behind CA:
                {
                    return distance(coplanar_pos, pos_c);
                }
                else  // Between C and A (overlapping zone):
                {
                    vector vec_ca_norm = normalize(vec_ca);
                    return distance(coplanar_pos, pos_c + min(length(vec_ca), dot(vec_cp, vec_ca_norm)) * vec_ca_norm);
                }
            }
            else  // Between B and C:
            {
                vector vec_bc_norm = normalize(vec_bc);
                return distance(coplanar_pos, pos_b + dot(vec_bp, vec_bc_norm) * vec_bc_norm);
            }
        }
        else
        {
            vector vec_ca = pos_a - pos_c;
            float dot_cn = dot(cross(vec_ca, vec_cp), normal);

            if (dot_cn <= 0)  // Outside of or on line CA:
            {
                if (dot(vec_cp, vec_ca) <= 0)  // Behind CA:
                {
                    return distance(coplanar_pos, pos_c);
                }
                else if (dot(vec_ap, vec_ca) >= 0)  // In front of CA:
                {
                    return distance(coplanar_pos, pos_a);
                }
                else  // Between C and A:
                {
                    vector vec_ca_norm = normalize(vec_ca);
                    return distance(coplanar_pos, pos_c + dot(vec_cp, vec_ca_norm) * vec_ca_norm);
                }
            }
            else  // Inside the triangle:
            {
                vector vec_ab_norm = normalize(vec_ab);
                vector vec_bc_norm = normalize(vec_bc);
                vector vec_ca_norm = normalize(vec_ca);

                return -min(distance(coplanar_pos, pos_a + dot(vec_ap, vec_ab_norm) * vec_ab_norm),
                            distance(coplanar_pos, pos_b + dot(vec_bp, vec_bc_norm) * vec_bc_norm),
                            distance(coplanar_pos, pos_c + dot(vec_cp, vec_ca_norm) * vec_ca_norm));
            }
        }
    }
}

float labs_pointtriedgedist(const int geometry, ptnum_a, ptnum_b, ptnum_c; const vector coplanar_pos)
{
    return labs_pointtriedgedist(vector(point(geometry, "P", ptnum_a)),
                                 vector(point(geometry, "P", ptnum_b)),
                                 vector(point(geometry, "P", ptnum_c)), coplanar_pos);
}

float labs_pointtriedgedist(const int geometry, primnum; const vector coplanar_pos)
{
    return labs_pointtriedgedist(geometry,
                                 primpoint(geometry, primnum, 0),
                                 primpoint(geometry, primnum, 1),
                                 primpoint(geometry, primnum, 2), coplanar_pos);
}


// Point-Triangle-Edge Projection

float labs_pointtriedgeproj(const vector pos_a, pos_b, pos_c, coplanar_pos; export vector nearest_pos)
{
    vector vec_ab = pos_b - pos_a;
    vector vec_bc = pos_c - pos_b;
    vector normal = cross(vec_ab, vec_bc);
    vector vec_ap = coplanar_pos - pos_a;
    vector vec_bp = coplanar_pos - pos_b;
    float dot_an = dot(cross(vec_ab, vec_ap), normal);

    if (dot_an <= 0)  // Outside of or on line AB:
    {
        if (dot(vec_ap, vec_ab) <= 0)  // Behind AB:
        {
            vector vec_ca = pos_a - pos_c;

            if (dot(vec_ap, vec_ca) >= 0)  // In front of CA:
            {
                nearest_pos = pos_a;
                return distance(coplanar_pos, nearest_pos);
            }
            else  // Between C and A (overlapping zone):
            {
                vector vec_ca_norm = normalize(vec_ca);
                nearest_pos = pos_c + max(0, dot(coplanar_pos - pos_c, vec_ca_norm)) * vec_ca_norm;
                return distance(coplanar_pos, nearest_pos);
            }
        }
        else if (dot(vec_bp, vec_ab) >= 0)  // In front of AB:
        {
            if (dot(vec_bp, vec_bc) <= 0)  // Behind BC:
            {
                nearest_pos = pos_b;
                return distance(coplanar_pos, nearest_pos);
            }
            else  // Between B and C (overlapping zone):
            {
                vector vec_bc_norm = normalize(vec_bc);
                nearest_pos = pos_b + min(length(vec_bc), dot(vec_bp, vec_bc_norm)) * vec_bc_norm;
                return distance(coplanar_pos, nearest_pos);
            }
        }
        else  // Between A and B:
        {
            vector vec_ab_norm = normalize(vec_ab);
            nearest_pos = pos_a + dot(vec_ap, vec_ab_norm) * vec_ab_norm;
            return distance(coplanar_pos, nearest_pos);
        }
    }
    else
    {
        float dot_bn = dot(cross(vec_bc, vec_bp), normal);
        vector vec_cp = coplanar_pos - pos_c;

        if (dot_bn <= 0)  // Outside of or on line BC:
        {
            if (dot(vec_bp, vec_bc) <= 0)  // Behind BC:
            {
                nearest_pos = pos_b;
                return distance(coplanar_pos, nearest_pos);
            }
            else if (dot(vec_cp, vec_bc) >= 0)  // In front of BC:
            {
                vector vec_ca = pos_a - pos_c;

                if (dot(vec_cp, vec_ca) <= 0)  // Behind CA:
                {
                    nearest_pos = pos_c;
                    return distance(coplanar_pos, nearest_pos);
                }
                else  // Between C and A (overlapping zone):
                {
                    vector vec_ca_norm = normalize(vec_ca);
                    nearest_pos = pos_c + min(length(vec_ca), dot(vec_cp, vec_ca_norm)) * vec_ca_norm;
                    return distance(coplanar_pos, nearest_pos);
                }
            }
            else  // Between B and C:
            {
                vector vec_bc_norm = normalize(vec_bc);
                nearest_pos = pos_b + dot(vec_bp, vec_bc_norm) * vec_bc_norm;
                return distance(coplanar_pos, nearest_pos);
            }
        }
        else
        {
            vector vec_ca = pos_a - pos_c;
            float dot_cn = dot(cross(vec_ca, vec_cp), normal);

            if (dot_cn <= 0)  // Outside of or on line CA:
            {
                if (dot(vec_cp, vec_ca) <= 0)  // Behind CA:
                {
                    nearest_pos = pos_c;
                    return distance(coplanar_pos, nearest_pos);
                }
                else if (dot(vec_ap, vec_ca) >= 0)  // In front of CA:
                {
                    nearest_pos = pos_a;
                    return distance(coplanar_pos, nearest_pos);
                }
                else  // Between C and A:
                {
                    vector vec_ca_norm = normalize(vec_ca);
                    nearest_pos = pos_c + dot(vec_cp, vec_ca_norm) * vec_ca_norm;
                    return distance(coplanar_pos, nearest_pos);
                }
            }
            else  // Inside the triangle:
            {
                vector vec_ab_norm = normalize(vec_ab);
                vector vec_bc_norm = normalize(vec_bc);
                vector vec_ca_norm = normalize(vec_ca);

                vector nearest_pos_ab = pos_a + dot(vec_ap, vec_ab_norm) * vec_ab_norm;
                vector nearest_pos_bc = pos_b + dot(vec_bp, vec_bc_norm) * vec_bc_norm;
                vector nearest_pos_ca = pos_c + dot(vec_cp, vec_ca_norm) * vec_ca_norm;

                float dist_ab = distance(coplanar_pos, nearest_pos_ab);
                float dist_bc = distance(coplanar_pos, nearest_pos_bc);
                float dist_ca = distance(coplanar_pos, nearest_pos_ca);

                if (dist_ab <= dist_bc && dist_ab <= dist_ca)
                {
                    nearest_pos = nearest_pos_ab;
                    return -dist_ab;
                }
                else if (dist_bc <= dist_ab && dist_bc <= dist_ca)
                {
                    nearest_pos = nearest_pos_bc;
                    return -dist_bc;
                }
                else
                {
                    nearest_pos = nearest_pos_ca;
                    return -dist_ca;
                }
            }
        }
    }
}

float labs_pointtriedgeproj(const int geometry, ptnum_a, ptnum_b, ptnum_c; const vector coplanar_pos; export vector nearest_pos)
{
    return labs_pointtriedgeproj(vector(point(geometry, "P", ptnum_a)),
                                 vector(point(geometry, "P", ptnum_b)),
                                 vector(point(geometry, "P", ptnum_c)), coplanar_pos, nearest_pos);
}

float labs_pointtriedgeproj(const int geometry, primnum; const vector coplanar_pos; export vector nearest_pos)
{
    return labs_pointtriedgeproj(geometry,
                                 primpoint(geometry, primnum, 0),
                                 primpoint(geometry, primnum, 1),
                                 primpoint(geometry, primnum, 2), coplanar_pos, nearest_pos);
}


// Point-Triangle Distance

float labs_pointtridist(const vector pos_a, pos_b, pos_c, pos)
{
    vector coplanar_pos;
    float signed_pt_plane_dist = labs_pointplaneproj(pos_a, pos_b, pos_c, pos, coplanar_pos);

    if (labs_isoutsidetri(pos_a, pos_b, pos_c, coplanar_pos) <= 0)  // Coplanar position is not outside triangle
    {
        return abs(signed_pt_plane_dist);
    }
    else  // Coplanar position is outside triangle
    {
        float pt_tri_edge_dist = labs_pointtriedgedist(pos_a, pos_b, pos_c, coplanar_pos);
        return sqrt(signed_pt_plane_dist * signed_pt_plane_dist + pt_tri_edge_dist * pt_tri_edge_dist);
    }
}

float labs_pointtridist(const int geometry; const int ptnum_a, ptnum_b, ptnum_c; const vector pos)
{
    return labs_pointtridist(vector(point(geometry, "P", ptnum_a)),
                             vector(point(geometry, "P", ptnum_b)),
                             vector(point(geometry, "P", ptnum_c)), pos);
}

float labs_pointtridist(const int geometry, primnum; const vector pos)
{
    return labs_pointtridist(geometry,
                             primpoint(geometry, primnum, 0),
                             primpoint(geometry, primnum, 1),
                             primpoint(geometry, primnum, 2), pos);
}


// Point-Triangle Projection

float labs_pointtriproj(const vector pos_a, pos_b, pos_c, pos; export vector nearest_pos)
{
    vector coplanar_pos;
    float signed_pt_plane_dist = labs_pointplaneproj(pos_a, pos_b, pos_c, pos, coplanar_pos);

    if (labs_isoutsidetri(pos_a, pos_b, pos_c, coplanar_pos) <= 0)  // Coplanar position is not outside triangle
    {
        nearest_pos = coplanar_pos;
        return abs(signed_pt_plane_dist);
    }
    else  // Coplanar position is outside triangle
    {
        float pt_tri_edge_dist = labs_pointtriedgeproj(pos_a, pos_b, pos_c, coplanar_pos, nearest_pos);
        return sqrt(signed_pt_plane_dist * signed_pt_plane_dist + pt_tri_edge_dist * pt_tri_edge_dist);
    }
}

float labs_pointtriproj(const int geometry; const int ptnum_a, ptnum_b, ptnum_c; const vector pos; export vector nearest_pos)
{
    return labs_pointtriproj(vector(point(geometry, "P", ptnum_a)),
                             vector(point(geometry, "P", ptnum_b)),
                             vector(point(geometry, "P", ptnum_c)), pos, nearest_pos);
}

float labs_pointtriproj(const int geometry, primnum; const vector pos; export vector nearest_pos)
{
    return labs_pointtriproj(geometry,
                             primpoint(geometry, primnum, 0),
                             primpoint(geometry, primnum, 1),
                             primpoint(geometry, primnum, 2), pos, nearest_pos);
}


// Triangle Circumcenter

vector labs_circumcenter_tri(const vector pos_a, pos_b, pos_c; export float radius)
{
    vector vec_ab = pos_b - pos_a;
    vector vec_ac = pos_c - pos_a;
    vector cross_abac = cross(vec_ab, vec_ac);

    vector a_to_center = (dot(vec_ac, vec_ac) * cross(cross_abac, vec_ab) + dot(vec_ab, vec_ab) * cross(vec_ac, cross_abac)) /
                         (2.0 * dot(cross_abac, cross_abac));

    radius = length(a_to_center);
    return pos_a + a_to_center;
}


vector labs_circumcenter_tri(const int geometry, ptnum_a, ptnum_b, ptnum_c; export float radius)
{
    return labs_circumcenter_tri(vector(point(geometry, "P", ptnum_a)),
                                 vector(point(geometry, "P", ptnum_b)),
                                 vector(point(geometry, "P", ptnum_c)), radius);
}

vector labs_circumcenter_tri(const int geometry, primnum; export float radius)
{
    return labs_circumcenter_tri(geometry,
                                 primpoint(geometry, primnum, 0),
                                 primpoint(geometry, primnum, 1),
                                 primpoint(geometry, primnum, 2), radius);
}


// Triangle Bounding Sphere

vector labs_boundsphere_tri(const vector pos_a, pos_b, pos_c; export float radius)
{
    float dist_ab = distance(pos_a, pos_b);
    float dist_bc = distance(pos_b, pos_c);
    float dist_ca = distance(pos_c, pos_a);

    if (dist_ab >= dist_bc && dist_ab >= dist_ca)
    {
        radius = 0.5 * dist_ab;
        return 0.5 * (pos_a + pos_b);
    }
    else if (dist_bc >= dist_ab && dist_bc >= dist_ca)
    {
        radius = 0.5 * dist_bc;
        return 0.5 * (pos_b + pos_c);
    }
    else
    {
        radius = 0.5 * dist_ca;
        return 0.5 * (pos_c + pos_a);
    }
}


vector labs_boundsphere_tri(const int geometry, ptnum_a, ptnum_b, ptnum_c; export float radius)
{
    return labs_boundsphere_tri(vector(point(geometry, "P", ptnum_a)),
                                vector(point(geometry, "P", ptnum_b)),
                                vector(point(geometry, "P", ptnum_c)), radius);
}

vector labs_boundsphere_tri(const int geometry, primnum; export float radius)
{
    return labs_boundsphere_tri(geometry,
                                primpoint(geometry, primnum, 0),
                                primpoint(geometry, primnum, 1),
                                primpoint(geometry, primnum, 2), radius);
}


// Angle between Directions

float labs_anglebetween(const vector unit_vec_a, unit_vec_b; const int in_degrees)
{
    return in_degrees ?
           degrees(acos(dot(unit_vec_a, unit_vec_b))) :
           acos(dot(unit_vec_a, unit_vec_b));
}


// Rotate Vector

vector labs_rotatevector(const vector vec; const float angle; const vector unit_axis; const int in_degrees)
{
    return qrotate(quaternion(in_degrees ? radians(angle) : angle, unit_axis), vec);
}

vector labs_rotatevector(const vector vec, start_vec, end_vec)
{
    return qrotate(dihedral(start_vec, end_vec), vec);
}


// Rotate Vector 2D

vector2 labs_rotatevector2d(const vector2 vec2d; const float angle; const int in_degrees)
{
    float angle_rad = in_degrees ? radians(angle) : angle;
    float cos_angle = cos(angle_rad);
    float sin_angle = sin(angle_rad);

    return set(cos_angle * vec2d.x - sin_angle * vec2d.y,
               sin_angle * vec2d.x + cos_angle * vec2d.y);
}

vector2 labs_rotatevector2d(const vector2 vec2d, start_vec2d, end_vec2d)
{
    return (vector2)labs_rotatevector((vector)vec2d, (vector)start_vec2d, (vector)end_vec2d);
}


// Get Non-collinear

vector labs_getnoncollinear(const vector vec)
{
    return set(vec.z, vec.x, -vec.y);
}


#endif