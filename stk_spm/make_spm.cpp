#include <aabbox3d.h>
#include <algorithm>
#include <array>
#include <bitset>
#include <cassert>
#include <cmath>
#include <cstring>
#include <fstream>
#include <functional>
#include <expat.h>
#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>
#include <glm/gtx/quaternion.hpp>
#include <glm/gtx/transform.hpp>
#include <numeric>
#include <set>
#include <sstream>
#include <string>
#include <triangle3d.h>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <vector2d.h>
#include <vector3d.h>
#include <SColor.h>

const uint8_t VERSION = 1;

using namespace irr;

void toHalfFloat(void *dst, float f)
{
    uint16_t hf = glm::detail::toFloat16(f);
    memcpy(dst, &hf, 2);
}

void mdm_normalNativeTo10_10_10_2(void *dst, float *src)
{
    int part;
    uint32_t sum;
    float v;
    sum = 0;
    v = fminf(1.0, fmaxf(-1.0, src[0]));
    if (v > 0.0)
    {
        part = (int)((v * 511.0) + 0.5);
    }
    else
    {
        part = (int)((v * 512.0) - 0.5);
    }
    sum |= ((uint32_t)part & 1023) << 0;
    v = fminf(1.0, fmaxf(-1.0, src[1]));
    if (v > 0.0)
    {
        part = (int)((v * 511.0) + 0.5);
    }
    else
    {
        part = (int)((v * 512.0) - 0.5);
    }
    sum |= ((uint32_t)part & 1023) << 10;
    v = fminf(1.0, fmaxf(-1.0, src[2]));
    if (v > 0.0)
    {
        part = (int)((v * 511.0) + 0.5);
    }
    else
    {
        part = (int)((v * 512.0) - 0.5);
    }
    sum |= ((uint32_t)part & 1023) << 20;
    v = fminf(1.0, fmaxf(-1.0, src[3]));
    if (v > 0.0)
    {
        part = (int)((v * 1.0) + 0.5);
    }
    else
    {
        part = (int)((v * 2.0) - 0.5);
    }
    sum |= ((uint32_t)part & 3) << 30;
    memcpy(dst, &sum, 4);
}

struct JointData
{
    std::vector<std::pair<std::string, float> > m_data;
};

struct BlenderExportData
{
    float data_float[13];
    std::string uv_one_name, uv_two_name, arm_name;
    float weights[4];
    int32_t bone_idx[4];
    JointData* joint_data;
};

struct SPMVertex
{
    SPMVertex()
    {
        m_tangent.set(0.0f, 0.0f, 0.0f);
        m_bitangent.set(0.0f, 0.0f, 0.0f);
    }
    SPMVertex(float x, float y, float z, float nx, float ny, float nz,
              video::SColor c, float tu, float tv, float tu_2, float tv_2,
              int32_t bone_idx[4], float weights[4])
        : m_position(x, y, z), m_normal(nx, ny, nz), m_color(c), m_uv_one(tu, tv),
          m_uv_two(tu_2, tv_2)
    {
        m_tangent.set(0.0f, 0.0f, 0.0f);
        m_bitangent.set(0.0f, 0.0f, 0.0f);
        m_bone_idx[0] = bone_idx[0];
        m_bone_idx[1] = bone_idx[1];
        m_bone_idx[2] = bone_idx[2];
        m_bone_idx[3] = bone_idx[3];
        memcpy(m_weights, weights, 16);
    }
    core::vector3df m_position, m_normal, m_tangent, m_bitangent;
    video::SColor m_color;
    core::vector2df m_uv_one, m_uv_two;
    int16_t m_bone_idx[4];
    float m_weights[4];
    mutable std::pair<core::vector3df, int> m_tangent_cal, m_bitangent_cal;
    bool operator == (const SPMVertex& other) const
    {
        return ((m_position == other.m_position) && (m_normal == other.m_normal) &&
            (m_tangent == other.m_tangent) && (m_bitangent == other.m_bitangent) &&
            (m_color == other.m_color) && (m_uv_one == other.m_uv_one) &&
            (m_uv_two == other.m_uv_two) && (m_weights[0] == other.m_weights[0]) &&
            (m_weights[1] == other.m_weights[1]) && (m_weights[2] == other.m_weights[2]) &&
            (m_weights[3] == other.m_weights[3]) && (m_bone_idx[0] == other.m_bone_idx[0]) &&
            (m_bone_idx[1] == other.m_bone_idx[1]) && (m_bone_idx[2] == other.m_bone_idx[2]) &&
            (m_bone_idx[3] == other.m_bone_idx[3]));
    }
};

struct Hasher
{
    std::size_t operator()(const SPMVertex& k) const
    {
        return ((std::hash<float>()(k.m_position.X)
            ^ (std::hash<float>()(k.m_normal.X) << 1)) >> 1)
            ^ (std::hash<float>()(k.m_position.Z) << 1);
    }
};

struct Quad
{
    core::vector3df m_p[4];
    core::vector3df m_normal;
    core::vector3df m_trace_pos;
    std::vector<int> m_sector_belong;
    Quad(core::vector3df p1, core::vector3df p2, core::vector3df p3,
         core::vector3df p4)
    {
        m_p[0] = p1;
        m_p[1] = p2;
        m_p[2] = p3;
        m_p[3] = p4;
        core::triangle3df tri1(p1, p2, p3);
        core::triangle3df tri2(p1, p3, p4);
        core::vector3df normal1 = tri1.getNormal();
        core::vector3df normal2 = tri2.getNormal();
        m_normal = -0.5f * (normal1 + normal2);
        m_normal.normalize();
        core::vector3df center = 0.25f * (p1 + p2 + p3 + p4);
        m_trace_pos = center + m_normal;
    }
};

struct Triangle
{
    bool m_partitioned;
    SPMVertex m_v[3];
    const SPMVertex& operator[](int n) const { return m_v[n]; }
    SPMVertex& operator[](int n) { return m_v[n]; }
    std::string m_tex_one, m_tex_two, m_name_cmp;
    inline float getArea() const
    {
        return (m_v[1].m_position - m_v[0].m_position).crossProduct
            (m_v[2].m_position - m_v[0].m_position).getLength() * 0.5f;
    }
    core::vector3df getCenter() const
    {
        return (m_v[0].m_position + m_v[1].m_position +
            m_v[2].m_position) / 3.0f;
    }
    Triangle(SPMVertex* v, const std::string& tex_one,
             const std::string& tex_two)
    {
        m_v[0] = v[0];
        m_v[1] = v[1];
        m_v[2] = v[2];
        m_tex_one = tex_one;
        m_tex_two = tex_two;
        m_name_cmp = m_tex_one + m_tex_two;
        m_partitioned = false;
    }
    Triangle(const SPMVertex& v1, const SPMVertex& v2, const SPMVertex& v3,
             const std::string& tex_one, const std::string& tex_two)
    {
        m_v[0] = v1;
        m_v[1] = v2;
        m_v[2] = v3;
        m_tex_one = tex_one;
        m_tex_two = tex_two;
        m_name_cmp = m_tex_one + m_tex_two;
        m_partitioned = false;
    }
    inline bool insideBox(const core::aabbox3df& box) const
    {
        for (unsigned int i = 0; i < 3; i++)
        {
            if (!box.isPointInside(m_v[i].m_position))
            {
                return false;
            }
        }
        return true;
    }
    inline bool insideBoxOnePoint(const core::aabbox3df& box) const
    {
        for (unsigned int i = 0; i < 3; i++)
        {
            if (box.isPointInside(m_v[i].m_position))
            {
                return true;
            }
        }
        return false;
    }
};

std::set<std::string> g_transparent_mat;

void loadMat(void* data, const char* element, const char** attribute)
{
    if (strcmp(element, "material") == 0)
    {
        std::string mat_name;
        std::string shader_type;
        for (int i = 0; attribute[i]; i += 2)
        {
            if (strcmp(attribute[i], "name") == 0)
            {
                mat_name = attribute[i + 1];
            }
            if (strcmp(attribute[i], "shader") == 0)
            {
                shader_type = attribute[i + 1];
            }
        }
        if (shader_type == "additive" || shader_type == "alphablend" ||
            shader_type == "alphatest" || shader_type == "grass")
        {
            g_transparent_mat.insert(mat_name);
        }
    }
}

void initXML(const std::vector<char>& bytes,
             void(*cb)(void* data, const char* element, const char** attr))
{
    XML_Parser parser = XML_ParserCreate(NULL);
    XML_SetElementHandler(parser, cb, NULL);
    if (XML_Parse(parser, bytes.data(), bytes.size(), XML_TRUE)
        == XML_STATUS_ERROR)
    {
        printf("Error: %s\n", XML_ErrorString(XML_GetErrorCode(parser)));
        return;
    }
    XML_ParserFree(parser);
}

void initMaterials(const std::string& path)
{
    std::string g_mat = path.substr(0, path.find_last_of("\\/"));
    g_mat = g_mat.substr(0, g_mat.find_last_of("\\/"));
    std::ifstream mat_file_g(g_mat + "/textures/materials.xml",
        std::ios::binary);
    if (!mat_file_g.is_open())
    {
        printf("Missing global materials file.\n");
        return;
    }
    std::vector<char> mat_global((std::istreambuf_iterator<char>(mat_file_g)),
        std::istreambuf_iterator<char>());
    initXML(mat_global, loadMat);

    std::ifstream mat_file_t(path + "/materials.xml", std::ios::binary);
    if (!mat_file_t.is_open())
    {
        printf("Missing track materials file.\n");
        return;
    }
    std::vector<char> mat_track((std::istreambuf_iterator<char>(mat_file_t)),
        std::istreambuf_iterator<char>());
    initXML(mat_track, loadMat);
}

std::vector<Quad> g_quads;

void initQuadGraph(void* data, const char* element, const char** attribute)
{
    if (strcmp(element, "quad") == 0)
    {
        core::vector3df v[4];
        int j = 0;
        for (int i = 0; attribute[i]; i += 2)
        {
            std::string val = attribute[i + 1];
            bool use_existing = val.find_first_of(":") != std::string::npos;
            std::istringstream iss(val);
            if (strcmp(attribute[i], "p0") == 0 ||
                strcmp(attribute[i], "p1") == 0 ||
                strcmp(attribute[i], "p2") == 0 ||
                strcmp(attribute[i], "p3") == 0)
            {
                if (use_existing)
                {
                    std::vector<unsigned> id;
                    unsigned num;
                    while (iss >> num)
                    {
                        id.push_back(num);
                        if (iss.peek() == ':')
                        {
                            iss.ignore();
                        }
                    }
                    assert(id.size() == 2);
                    assert(id[0] < g_quads.size());
                    v[j] = g_quads[id[0]].m_p[id[1]];
                }
                else
                {
                    iss >> v[j].X >> v[j].Y >> v[j].Z;
                }
                j++;
            }
        }
        g_quads.push_back(Quad(v[0], v[1], v[2], v[3]));
    }
}

std::vector<core::vector3df> g_nav_vertices;
void initNavmesh(void* data, const char* element, const char** attribute)
{
    if (strcmp(element, "vertex") == 0)
    {
        core::vector3df v;
        for (int i = 0; attribute[i]; i += 2)
        {
            if (strcmp(attribute[i], "x") == 0)
            {
                std::istringstream iss(attribute[i + 1]);
                iss >> v.X;
            }
            else if (strcmp(attribute[i], "y") == 0)
            {
                std::istringstream iss(attribute[i + 1]);
                iss >> v.Y;
            }
            else if (strcmp(attribute[i], "z") == 0)
            {
                std::istringstream iss(attribute[i + 1]);
                iss >> v.Z;
            }
        }
        g_nav_vertices.push_back(v);
    }
    else if (strcmp(element, "face") == 0)
    {
        unsigned j, k, l, m = 9999999;
        for (int i = 0; attribute[i]; i += 2)
        {
            if (strcmp(attribute[i], "indices") == 0)
            {
                std::istringstream iss(attribute[i + 1]);
                iss >> j >> k >> l >> m;
            }
        }
        assert(j < g_nav_vertices.size());
        assert(k < g_nav_vertices.size());
        assert(l < g_nav_vertices.size());
        assert(m < g_nav_vertices.size());
        g_quads.push_back(Quad(g_nav_vertices[j], g_nav_vertices[k],
            g_nav_vertices[l], g_nav_vertices[m]));
    }
}

void initQuads(const std::string& path)
{
    std::ifstream qg(path + "/quads.xml", std::ios::binary);
    if (qg.is_open())
    {
        std::vector<char> bytes((std::istreambuf_iterator<char>(qg)),
            std::istreambuf_iterator<char>());
        initXML(bytes, initQuadGraph);
    }
    else
    {
        std::ifstream navmesh(path + "/navmesh.xml", std::ios::binary);
        if (navmesh.is_open())
        {
            std::vector<char> bytes((std::istreambuf_iterator<char>(navmesh)),
                std::istreambuf_iterator<char>());
            initXML(bytes, initNavmesh);
        }
    }
}

struct LocRotScale
{
    glm::vec3 m_loc;
    glm::quat m_rot;
    glm::vec3 m_scale;
};

struct InArm
{
    uint32_t m_non_animated_frame;
    std::string m_arm_name;
    std::unordered_map<std::string, int> m_bone_names;
    std::vector<std::tuple<std::string, int, LocRotScale> > m_loc_lrs;
    std::vector<std::pair<int, std::vector<std::tuple<std::string, std::string, int,
        LocRotScale> > > > m_poses;
};

void writeBBox(std::ofstream& mesh, const core::aabbox3df& box)
{
    float box_array[6] = { box.MinEdge.X, box.MinEdge.Y, box.MinEdge.Z,
        box.MaxEdge.X, box.MaxEdge.Y, box.MaxEdge.Z };
    mesh.write((char*)box_array, 24);
}

void writeHeader(std::ofstream& mesh, const std::string& header,
                 bool export_normal, bool export_vcolor,
                 bool export_tangent)
{
    std::string real_header = "SP";
    mesh << real_header;
    // 5 bit version, 3 bit type : SPMS SPMA SPMN
    uint8_t byte = VERSION;
    byte <<= 3;
    const uint8_t type_num = header == "SPMS" ? 0 : header == "SPMA" ? 1 : 2;
    byte |= type_num;
    mesh.write((char*)&byte, 1);
    std::bitset<8> misc_data;
    misc_data.reset();
    misc_data.set(0, export_normal);
    misc_data.set(1, export_vcolor);
    misc_data.set(2, export_tangent);
    byte = static_cast<uint8_t>(misc_data.to_ulong());
    mesh.write((char*)&byte, 1);
}

void writeArmData(std::ofstream& mesh, std::vector<InArm>& in_arms)
{
    uint8_t arm_size = (uint8_t)in_arms.size();
    mesh.write((char*)&arm_size, 1);
    uint16_t bind_frame = (uint16_t)in_arms[0].m_non_animated_frame;
    mesh.write((char*)&bind_frame, 2);
    unsigned accumlated_joint = 0;
    for (InArm& ia : in_arms)
    {
        unsigned cur_accumlated_joint = 0;
        for (auto& p : ia.m_bone_names)
        {
            if (p.second != -1)
            {
                p.second -= accumlated_joint;
                cur_accumlated_joint++;
            }
        }
        const uint16_t real_bones = (uint16_t)cur_accumlated_joint;
        accumlated_joint += cur_accumlated_joint;
        for (auto& p : ia.m_bone_names)
        {
            if (p.second == -1)
            {
                p.second = cur_accumlated_joint++;
            }
        }
        std::vector<std::pair<std::string, int> > written_bones;
        for (auto& p : ia.m_bone_names)
        {
            written_bones.emplace_back(p.first, p.second);
        }
        std::sort(written_bones.begin(), written_bones.end(),
            [](const std::pair<std::string, int>& a,
            const std::pair<std::string, int>& b)
            {
                return a.second < b.second;
            });
        mesh.write((char*)&real_bones, 2);
        uint16_t all_bones = (uint16_t)written_bones.size();
        mesh.write((char*)&all_bones, 2);
        for (auto& p : written_bones)
        {
            uint8_t char_num = (uint8_t)p.first.size();
            mesh.write((char*)&char_num, 1);
            mesh << p.first;
        }
        for (unsigned i = 0; i < ia.m_loc_lrs.size(); i++)
        {
            auto ret = ia.m_bone_names.find(std::get<0>(ia.m_loc_lrs[i]));
            assert(ret != ia.m_bone_names.end());
            std::get<1>(ia.m_loc_lrs[i]) = ret->second;
        }
        std::sort(ia.m_loc_lrs.begin(), ia.m_loc_lrs.end(),
            [](const std::tuple<std::string, int, LocRotScale>& a,
            std::tuple<std::string, int, LocRotScale>& b)
            {
                return std::get<1>(a) < std::get<1>(b);
            });
        for (unsigned i = 0; i < ia.m_loc_lrs.size(); i++)
        {
            mesh.write((char*)&(std::get<2>(ia.m_loc_lrs[i]).m_loc[0]), 40);
        }
        bool written_parent = false;
        for (auto& frame : ia.m_poses)
        {
            auto& p = frame.second;
            for (unsigned i = 0; i < p.size(); i++)
            {
                auto ret = ia.m_bone_names.find(std::get<0>(p[i]));
                assert(ret != ia.m_bone_names.end());
                std::get<2>(p[i]) = ret->second;
            }
            std::sort(p.begin(), p.end(),
                [](const std::tuple<std::string, std::string, int, LocRotScale>& a,
                const std::tuple<std::string, std::string, int, LocRotScale>& b)
                {
                    return std::get<2>(a) < std::get<2>(b);
                });
            if (!written_parent)
            {
                written_parent = true;
                for (auto& q : p)
                {
                    uint16_t bone_idx = -1;
                    auto ret = ia.m_bone_names.find(std::get<1>(q));
                    if (ret != ia.m_bone_names.end())
                    {
                        bone_idx = ret->second;
                    }
                    mesh.write((char*)&bone_idx, 2);
                }
                uint16_t frame_size = ia.m_poses.size();
                mesh.write((char*)&frame_size, 2);
            }
            uint16_t frame_index = (uint16_t)frame.first;
            mesh.write((char*)&frame_index, 2);
            for (auto& q : p)
            {
                mesh.write((char*)&(std::get<3>(q).m_loc[0]), 40);
            }
        }
    }
}

void calculateTangents(
    core::vector3df& normal,
    core::vector3df& tangent,
    core::vector3df& binormal,
    const core::vector3df& vt1, const core::vector3df& vt2, const core::vector3df& vt3, // vertices
    const core::vector2df& tc1, const core::vector2df& tc2, const core::vector2df& tc3) // texture coords
{
    core::vector3df v1 = vt1 - vt2;
    core::vector3df v2 = vt3 - vt1;
    normal = v2.crossProduct(v1);
    normal.normalize();

    // binormal

    f32 deltaX1 = tc1.X - tc2.X;
    f32 deltaX2 = tc3.X - tc1.X;
    binormal = (v1 * deltaX2) - (v2 * deltaX1);
    binormal.normalize();

    // tangent

    f32 deltaY1 = tc1.Y - tc2.Y;
    f32 deltaY2 = tc3.Y - tc1.Y;
    tangent = (v1 * deltaY2) - (v2 * deltaY1);
    tangent.normalize();

    // adjust

    core::vector3df txb = tangent.crossProduct(binormal);
    if (txb.dotProduct(normal) < 0.0f)
    {
        tangent *= -1.0f;
        binormal *= -1.0f;
    }
}

int main(int argc, char* argv[])
{
    if (argc != 7)
    {
        printf("Required 6 arguments.\n");
        return 0;
    }

    bool export_normal = strcmp(argv[4], "en") == 0;
    bool export_vcolor = strcmp(argv[5], "ev") == 0;
    bool export_tangent = strcmp(argv[6], "et") == 0;

    std::vector<BlenderExportData> bed;
    std::string mesh_data = argv[1];
    mesh_data += ".mesh_data";
    std::ifstream spm(mesh_data, std::ios::in | std::ios::binary);
    if (!spm.is_open())
    {
        printf("Mesh data not found.\n");
        return 0;
    }
    while (true)
    {
        struct TmpData
        {
            char uv_one_name[64];
            char uv_two_name[64];
            char arm_name[64];
        };
        TmpData td;
        BlenderExportData dat = {};
        spm.read((char*)&dat.data_float, 13 * 4);
        spm.read((char*)&td, sizeof(TmpData));
        if (spm.eof())
            break;
        dat.uv_one_name = td.uv_one_name;
        dat.uv_two_name = td.uv_two_name;
        dat.arm_name = td.arm_name;
        memset(dat.weights, 0.0f, 16);
        memset(dat.bone_idx, -1, 16);
        bed.push_back(dat);
    }
    std::remove(mesh_data.c_str());
    std::string path = argv[1];
    std::string header = strcmp(argv[2], "do-sp") == 0 ? "SPMS" : "SPMN";
    int arm_number = atoi(argv[3]);
    std::vector<InArm> in_arms;
    if (arm_number > 0)
    {
        std::vector<JointData> joint_data;
        std::string j_name = std::string(argv[1]) + ".joint_data";
        std::ifstream jf(j_name, std::ios::in | std::ios::binary);
        if (!jf.is_open())
        {
            printf("Joint data not found.\n");
            return 0;
        }
        while (true)
        {
            int32_t j_size;
            jf.read((char*)&j_size, 4);
            if (jf.eof())
                break;
            JointData j_data;
            for (int j_idx = 0; j_idx < j_size; j_idx++)
            {
                char joint_name[64];
                float weight;
                jf.read(joint_name, 64);
                jf.read((char*)&weight, 4);
                if (weight > 1.0f)
                {
                    weight = 1.0f;
                }
                j_data.m_data.emplace_back(joint_name, weight);
            }
            joint_data.push_back(j_data);
        }
        std::remove(j_name.c_str());
        assert(joint_data.size() == bed.size());
        for (unsigned i = 0; i < joint_data.size(); i++)
        {
            bed[i].joint_data = &joint_data[i];
        }
        header = "SPMA";
        for (int i = 0; i < arm_number; i++)
        {
            std::stringstream ss;
            ss << argv[1] << i << ".animated_data";
            std::ifstream am(ss.str(), std::ios::in | std::ios::binary);
            if (am.is_open())
            {
                InArm in_arm = {};
                char arm_name[64];
                am.read(arm_name, 64);
                in_arm.m_arm_name = arm_name;
                am.read((char*)&in_arm.m_non_animated_frame, 4);
                uint32_t number = 0;
                am.read((char*)&number, 4);
                for (unsigned bone = 0; bone < number; bone++)
                {
                    char bone_name[64];
                    LocRotScale lrs;
                    am.read(bone_name, 64);
                    am.read((char*)&lrs, 40);
                    in_arm.m_loc_lrs.emplace_back(bone_name, -1, lrs);
                }
                am.read((char*)&number, 4);
                std::pair<int, std::vector<std::tuple<std::string, std::string, int,
                    LocRotScale> > > cur_frame;
                for (unsigned pose = 0; pose < number; pose++)
                {
                    uint32_t frame_number = 0;
                    am.read((char*)&frame_number, 4);
                    cur_frame.first = frame_number;
                    uint32_t pose_number = 0;
                    am.read((char*)&pose_number, 4);
                    for (unsigned bone = 0; bone < pose_number; bone++)
                    {
                        char bone_name[64], parent_name[64];
                        LocRotScale lrs;
                        am.read(bone_name, 64);
                        am.read(parent_name, 64);
                        am.read((char*)&lrs, 40);
                        cur_frame.second.emplace_back(bone_name, parent_name, -1 , lrs);
                    }
                    if (in_arm.m_bone_names.empty())
                    {
                        for (auto& p : cur_frame.second)
                        {
                            in_arm.m_bone_names[std::get<0>(p)] = -1;
                        }
                    }
                    assert(cur_frame.second.size() == in_arm.m_loc_lrs.size());
                    in_arm.m_poses.emplace_back(std::move(cur_frame));
                    assert(cur_frame.second.empty());
                }
                in_arms.push_back(in_arm);
            }
            am.close();
            std::remove(ss.str().c_str());
        }
        int cur_bone_idx = 0;
        for (unsigned arm = 0; arm < in_arms.size(); arm++)
        {
            InArm& ia = in_arms[arm];
            for (BlenderExportData& data : bed)
            {
                if (ia.m_arm_name != data.arm_name)
                {
                    continue;
                }
                std::vector<std::pair<int, float> > new_joints_data;
                for (int j = 0; j < data.joint_data->m_data.size(); j++)
                {
                    auto ret = ia.m_bone_names.find(data.joint_data->m_data[j].first);
                    if (ret != ia.m_bone_names.end())
                    {
                        if (ret->second == -1)
                        {
                            ret->second = cur_bone_idx++;
                        }
                        if (data.joint_data->m_data[j].second > 0.0f)
                        {
                            new_joints_data.emplace_back(ret->second,
                                data.joint_data->m_data[j].second);
                        }
                    }
                }
                std::sort(new_joints_data.begin(), new_joints_data.end(),
                    [](const std::pair<int, float>& a,
                    const std::pair<int, float>& b)
                    {
                        return a.second > b.second;
                    });
                new_joints_data.resize(4, std::pair<int, float>(0, 0.0f));
                float total_weights = 0.0f;
                for (auto& p : new_joints_data)
                {
                    total_weights += p.second;
                }
                if (total_weights > 0.0f)
                {
                    for (auto& p : new_joints_data)
                    {
                        p.second /= total_weights;
                    }
                }
                /*for (auto& p : new_joints_data)
                {
                    printf("%f ", p.second);
                }
                printf("\n");*/
                data.weights[0] = new_joints_data[0].second;
                data.weights[1] = new_joints_data[1].second;
                data.weights[2] = new_joints_data[2].second;
                data.weights[3] = new_joints_data[3].second;
                data.bone_idx[0] = new_joints_data[0].first;
                data.bone_idx[1] = new_joints_data[1].first;
                data.bone_idx[2] = new_joints_data[2].first;
                data.bone_idx[3] = new_joints_data[3].first;
            }
        }
        bool has_no_arm = true;
        for (BlenderExportData& data : bed)
        {
            if (data.weights[0] != 0.0f)
            {
                has_no_arm = false;
            }
        }
        if (has_no_arm)
        {
            header = "SPMN";
        }
    }
    else if (header == "SPMS")
    {
        const std::string local_path = path.substr(0, path.find_last_of("\\/"));
        initMaterials(local_path);
        initQuads(local_path);
        if (g_quads.empty())
        {
            printf("Missing quad or navmesh file, won't do raytrace"
                " preprocessing.\n");
        }
    }

    std::vector<Triangle> tris;
    core::aabbox3df aabb;
    bool loaded_bbox = false;
    /*for (const Quad& q : g_quads)
    {
        video::SColor vc(255, 255, 255, 255);
        SPMVertex v[4];
        std::string uv_one, uv_two;
        v[0] = SPMVertex(q.m_p[0].X, q.m_p[0].Y, q.m_p[0].Z, q.m_normal.X,
            q.m_normal.Y, q.m_normal.Z, vc, 0, 0, 0, 0);
        v[1] = SPMVertex(q.m_p[1].X, q.m_p[1].Y, q.m_p[1].Z, q.m_normal.X,
            q.m_normal.Y, q.m_normal.Z, vc, 0, 0, 0, 0);
        v[2] = SPMVertex(q.m_p[2].X, q.m_p[2].Y, q.m_p[2].Z, q.m_normal.X,
            q.m_normal.Y, q.m_normal.Z, vc, 0, 0, 0, 0);
        v[3] = SPMVertex(q.m_p[3].X, q.m_p[3].Y, q.m_p[3].Z, q.m_normal.X,
            q.m_normal.Y, q.m_normal.Z, vc, 0, 0, 0, 0);
        aabb.addInternalPoint(q.m_p[0].X, q.m_p[0].Y, q.m_p[0].Z);
        tris.push_back(Triangle(v[2], v[1], v[0], uv_one, uv_two));
        tris.push_back(Triangle(v[3], v[2], v[0], uv_one, uv_two));
    }*/
    for (unsigned int i = 0; i < bed.size(); i += 3)
    {
        int k = 0;
        SPMVertex v[3];
        std::string uv_one, uv_two;
        for (unsigned int j = i; j < i + 3; j++)
        {
            uv_one = bed[j].uv_one_name;
            uv_two = bed[j].uv_two_name;
            video::SColorf vc(bed[j].data_float[10], bed[j].data_float[11],
                bed[j].data_float[12]);
            v[k] = SPMVertex(bed[j].data_float[0], bed[j].data_float[1],
                bed[j].data_float[2], bed[j].data_float[3], bed[j].data_float[4],
                bed[j].data_float[5], vc.toSColor(), bed[j].data_float[6],
                bed[j].data_float[7], bed[j].data_float[8],
                bed[j].data_float[9], bed[j].bone_idx, bed[j].weights);
            aabb.addInternalPoint(bed[j].data_float[0], bed[j].data_float[1],
                bed[j].data_float[2]);
            k++;
        }
        Triangle t = Triangle(v, uv_one, uv_two);
        tris.push_back(t);
        const core::aabbox3df cur_bbox(
            std::min({t[0].m_position.X, t[1].m_position.X,
            t[2].m_position.X}),
            std::min({t[0].m_position.Y, t[1].m_position.Y,
            t[2].m_position.Y}),
            std::min({t[0].m_position.Z, t[1].m_position.Z,
            t[2].m_position.Z}),
            std::max({t[0].m_position.X, t[1].m_position.X,
            t[2].m_position.X}),
            std::max({t[0].m_position.Y, t[1].m_position.Y,
            t[2].m_position.Y}),
            std::max({t[0].m_position.Z, t[1].m_position.Z,
            t[2].m_position.Z}));
         if (!loaded_bbox)
         {
             loaded_bbox = true;
             aabb = cur_bbox;
         }
         else
         {
             aabb.addInternalBox(cur_bbox);
         }
    }

    std::unordered_map<SPMVertex, uint32_t, Hasher> vert_map;
    std::vector<SPMVertex> vert;
    std::vector<uint32_t> idx;
    if (export_tangent)
    {
        // STK tangent calculation
        if (1)
        {
            for (auto& tri : tris)
            {
                for (unsigned int i = 0; i < 3; i++)
                {
                    SPMVertex& v = tri[i];
                    auto it = vert_map.find(v);
                    if (it == vert_map.end())
                    {
                        unsigned vert_loc = vert.size();
                        idx.push_back(vert_loc);
                        vert.push_back(v);
                        vert_map[v] = vert_loc;
                    }
                    else
                    {
                        idx.push_back(it->second);
                    }
                }
            }
            for (unsigned i = 0; i < idx.size(); i += 3)
            {
                core::vector3df local_normal, local_tangent, local_bitangent;
                calculateTangents(local_normal, local_tangent, local_bitangent,
                    (vert[idx[i + 0]]).m_position, (vert[idx[i + 1]]).m_position,
                    (vert[idx[i + 2]]).m_position, (vert[idx[i + 0]]).m_uv_one,
                    (vert[idx[i + 1]]).m_uv_one, (vert[idx[i + 2]]).m_uv_one);
                (vert[idx[i + 0]]).m_tangent_cal.first = local_tangent;
                (vert[idx[i + 0]]).m_bitangent_cal.first = local_bitangent;

                calculateTangents(local_normal, local_tangent, local_bitangent,
                    (vert[idx[i + 1]]).m_position, (vert[idx[i + 2]]).m_position,
                    (vert[idx[i + 0]]).m_position, (vert[idx[i + 1]]).m_uv_one,
                    (vert[idx[i + 2]]).m_uv_one, (vert[idx[i + 0]]).m_uv_one);
                (vert[idx[i + 1]]).m_tangent_cal.first = local_tangent;
                (vert[idx[i + 1]]).m_bitangent_cal.first = local_bitangent ;

                calculateTangents(local_normal, local_tangent, local_bitangent,
                    (vert[idx[i + 2]]).m_position, (vert[idx[i + 0]]).m_position,
                    (vert[idx[i + 1]]).m_position, (vert[idx[i + 2]]).m_uv_one,
                    (vert[idx[i + 0]]).m_uv_one, (vert[idx[i + 1]]).m_uv_one);
                (vert[idx[i + 2]]).m_tangent_cal.first = local_tangent;
                (vert[idx[i + 2]]).m_bitangent_cal.first = local_bitangent;
            }
            for (auto& tri : tris)
            {
                for (unsigned int i = 0; i < 3; i++)
                {
                    SPMVertex& v = tri[i];
                    auto it = vert_map.find(v);
                    assert(it != vert_map.end());
                    assert(tri[i].m_position == (vert[it->second]).m_position);
                    tri[i].m_tangent = (vert[it->second]).m_tangent_cal.first;
                    tri[i].m_bitangent = (vert[it->second]).m_bitangent_cal.first;
                }
            }
        }
        else
        {
            // Calculate smooth tangents and bitangents
            for (unsigned int i = 0; i < tris.size(); i++)
            {
                const core::vector3df& v0 = tris[i][0].m_position;
                const core::vector3df& v1 = tris[i][1].m_position;
                const core::vector3df& v2 = tris[i][2].m_position;
                const core::vector2df& uv0 = tris[i][0].m_uv_one;
                const core::vector2df& uv1 = tris[i][1].m_uv_one;
                const core::vector2df& uv2 = tris[i][2].m_uv_one;
                core::vector3df delta_position_one = v1 - v0;
                core::vector3df delta_position_two = v2 - v0;
                core::vector2df delta_uv_one = uv1 - uv0;
                core::vector2df delta_uv_two = uv2 - uv0;
                float den = (delta_uv_one.X * delta_uv_two.Y - delta_uv_one.Y *
                    delta_uv_two.X);
                if (den == 0.0f)
                    den = 0.000001f;
                float r = 1.0f / den;
                core::vector3df m_tangent_cal = ((delta_position_two * delta_uv_one.X -
                    delta_position_one * delta_uv_two.X) * r).normalize();
                core::vector3df m_bitangent_cal = ((delta_position_one * delta_uv_two.Y -
                    delta_position_two * delta_uv_one.Y) * r).normalize();
                tris[i][0].m_tangent_cal = std::make_pair(m_tangent_cal, 1);
                tris[i][1].m_tangent_cal = std::make_pair(m_tangent_cal, 1);
                tris[i][2].m_tangent_cal = std::make_pair(m_tangent_cal, 1);
                tris[i][0].m_bitangent_cal = std::make_pair(m_bitangent_cal, 1);
                tris[i][1].m_bitangent_cal = std::make_pair(m_bitangent_cal, 1);
                tris[i][2].m_bitangent_cal = std::make_pair(m_bitangent_cal, 1);
            }
            std::unordered_set<SPMVertex, Hasher> univert;
            for (auto& tri : tris)
            {
                for (unsigned i = 0; i < 3; i++)
                {
                    const SPMVertex& v = tri[i];
                    auto it = univert.find(v);
                    if (it == univert.end())
                    {
                        univert.insert(v);
                    }
                    else
                    {
                        it->m_tangent_cal = std::make_pair(v.m_tangent_cal.first +
                            it->m_tangent_cal.first, v.m_tangent_cal.second + it->m_tangent_cal.second);
                        it->m_bitangent_cal = std::make_pair(v.m_bitangent_cal.first +
                            it->m_bitangent_cal.first, v.m_bitangent_cal.second +
                            it->m_bitangent_cal.second);
                    }
                }
            }

            for (auto& tri : tris)
            {
                for (unsigned i = 0; i < 3; i++)
                {
                    const SPMVertex& v = tri[i];
                    auto it = univert.find(v);
                    assert(it != univert.end());
                    if (it->m_tangent_cal.second != -1)
                    {
                        it->m_tangent_cal = std::make_pair
                            ((it->m_tangent_cal.first / it->m_tangent_cal.second).normalize(), -1);
                        it->m_bitangent_cal = std::make_pair
                            ((it->m_bitangent_cal.first / it->m_bitangent_cal.second).normalize(),
                            -1);
                    }
                    tri[i].m_tangent = it->m_tangent_cal.first;
                    tri[i].m_bitangent = it->m_bitangent_cal.first;
                }
            }
        }
    }

    std::sort(tris.begin(), tris.end(),
        [](const Triangle& tri_a, const Triangle& tri_b)->bool
        {
            return tri_a.m_name_cmp < tri_b.m_name_cmp;
        });

    std::ofstream mesh(path, std::ios::out | std::ios::binary);
    if (!mesh.is_open())
    {
        return 1;
    }

    writeHeader(mesh, header, export_normal, export_vcolor, export_tangent);
    writeBBox(mesh, aabb);

    std::unordered_map<std::string, std::tuple<unsigned, std::string,
        std::string> > tex_map;
    std::string cur_tex = "NULL";
    unsigned tex = 0;
    for (unsigned int i = 0; i < tris.size(); i++)
    {
        if (cur_tex != tris[i].m_name_cmp)
        {
            tex_map.emplace(std::piecewise_construct,
                std::forward_as_tuple(tris[i].m_name_cmp),
                std::forward_as_tuple(tex++, tris[i].m_tex_one,
                tris[i].m_tex_two));
            cur_tex = tris[i].m_name_cmp;
        }
    }

    if (tex_map.size() > 65535)
    {
        printf("More than 65535 textures are used.\n");
        return 1;
    }

    const size_t total_tris = tris.size();
    std::vector<std::pair<std::vector<Triangle>, core::aabbox3df> > sectors;
    if (header == "SPMS")
    {
        std::vector<Triangle> cur_sector;
        const float sec_size = 100.0f;
        for (float x = aabb.MaxEdge.X; x > aabb.MinEdge.X; x -= sec_size)
        {
            for (float y = aabb.MaxEdge.Y; y > aabb.MinEdge.Y; y -= sec_size)
            {
                for (float z = aabb.MaxEdge.Z; z > aabb.MinEdge.Z; z -= sec_size)
                {
                    cur_sector.clear();
                    core::aabbox3df cmp_box =
                        core::aabbox3df(x - sec_size, y - sec_size, z - sec_size,
                        x, y, z);
                    auto partition = std::partition(tris.begin(), tris.end(),
                        [&cmp_box](const Triangle& t)->bool
                        {
                            if (t.m_partitioned)
                            {
                                return false;
                            }
                            return t.insideBox(cmp_box);
                        });
                    const unsigned pred_num = std::distance(tris.begin(),
                        partition);
                    for (unsigned i = 0; i < pred_num; i++)
                    {
                        const Triangle& t = tris[i];
                        cur_sector.push_back(t);
                        tris[i].m_partitioned = true;
                    }
                    sectors.emplace_back(std::move(cur_sector), cmp_box);
                    assert(cur_sector.empty());
                }
            }
        }

        tris.erase(std::remove_if(tris.begin(), tris.end(),
            [](const Triangle& t)->bool
            {
                return t.m_partitioned;
            }), tris.end());

        int overlap_limit = 0;
        float each_overlap = 1.0f;
        bool end = false;
        while (!end)
        {
            overlap_limit += each_overlap;
            if (overlap_limit > 20)
            {
                end = true;
            }
            for (auto& p : sectors)
            {
                if (!end)
                {
                    p.second.addInternalPoint(p.second.MaxEdge +
                        core::vector3df(each_overlap));
                    p.second.addInternalPoint(p.second.MinEdge -
                        core::vector3df(each_overlap));
                }
                if (p.first.empty())
                {
                    continue;
                }
                for (unsigned i = 0; i < tris.size(); i++)
                {
                    if (tris[i].m_partitioned)
                    {
                        continue;
                    }
                    if (tris[i].insideBox(p.second))
                    {
                        tris[i].m_partitioned = true;
                        p.first.push_back(tris[i]);
                    }
                }
            }
        }

        tris.erase(std::remove_if(tris.begin(), tris.end(),
            [](const Triangle& t)->bool
            {
                return t.m_partitioned;
            }), tris.end());

        if (tris.size() > 0)
        {
            printf("%lu triangle(s) too large to fit in any sector.\n",
                tris.size());
        }
        sectors.emplace(sectors.begin(), std::move(tris),
            core::aabbox3df(0, 0, 0, 0, 0, 0));

        size_t partitioned_tris = std::accumulate(sectors.begin(), sectors.end(),
            0, [](size_t current_sum, const std::pair<std::vector<Triangle>,
            core::aabbox3df>& p)
            {
                return current_sum + p.first.size();
            });
        assert(partitioned_tris == total_tris);
    }
    else
    {
        // For mesh without SP, just emplace all triangles
        sectors.emplace_back(std::move(tris), aabb);
    }

    if (sectors.size() > 65535)
    {
        printf("More than 65535 sectors.\n");
        return 1;
    }
    else
    {
        printf("%lu sectors.\n", sectors.size());
    }

    uint16_t size_num = tex_map.size();
    mesh.write((char*)&size_num, 2);
    std::vector<std::tuple<unsigned, std::string, std::string> > tex_names;
    for (auto& p : tex_map)
    {
        tex_names.emplace_back(std::get<0>(p.second),
            std::get<1>(p.second), std::get<2>(p.second));
    }
    std::sort(tex_names.begin(), tex_names.end(),
        [](const std::tuple<unsigned, std::string, std::string>& a,
           const std::tuple<unsigned, std::string, std::string>& b)->bool
        {
            return std::get<0>(a) < std::get<0>(b);
        });
    assert(tex_names.size() == tex_map.size());
    for (auto& p : tex_names)
    {
        uint8_t char_num = std::get<1>(p).size();
        mesh.write((char*)&char_num, 1);
        mesh << std::get<1>(p);
        char_num = std::get<2>(p).size();
        mesh.write((char*)&char_num, 1);
        mesh << std::get<2>(p);
    }

    size_num = sectors.size();
    mesh.write((char*)&size_num, 2);
    for (unsigned sec_num = 0; sec_num < sectors.size(); sec_num++)
    {
        auto& s = sectors[sec_num];
        if (s.first.empty())
        {
            assert(header == "SPMS");
            size_num = 0;
            mesh.write((char*)&size_num, 2);
            writeBBox(mesh, s.second);
            continue;
        }
        std::sort(s.first.begin(), s.first.end(),
            [](const Triangle& tri_a, const Triangle& tri_b)->bool
            {
                return tri_a.m_name_cmp < tri_b.m_name_cmp;
            });
        std::string cur_tex = "NULL";
        std::vector<std::tuple<unsigned, unsigned,
            bool/*uv_1?*/, bool/*uv_2?*/> > offsets;
        unsigned start = 0;
        for (auto it = s.first.begin(); it != s.first.end(); it++)
        {
            if (cur_tex != it->m_name_cmp)
            {
                cur_tex = it->m_name_cmp;
                auto tup = tex_map.find(it->m_name_cmp);
                assert(tup != tex_map.end());
                offsets.emplace_back(start, std::get<0>(tup->second),
                    !it->m_tex_one.empty(), !it->m_tex_two.empty());
            }
            start++;
        }
        size_num = offsets.size();
        mesh.write((char*)&size_num, 2);
        for (unsigned offset = 0; offset < offsets.size(); offset++)
        {
            vert_map.clear();
            vert.clear();
            idx.clear();
            unsigned start = std::get<0>(offsets[offset]);
            unsigned end = offset + 1 == offsets.size() ? s.first.size() :
                std::get<0>(offsets[offset + 1]);
            for (; start < end; start++)
            {
                for (unsigned int i = 0; i < 3; i++)
                {
                    const SPMVertex& v = s.first[start][i];
                    auto it = vert_map.find(v);
                    if (it == vert_map.end())
                    {
                        unsigned vert_loc = vert.size();
                        idx.push_back(vert_loc);
                        vert.push_back(v);
                        vert_map[v] = vert_loc;
                    }
                    else
                    {
                        idx.push_back(it->second);
                    }
                }
            }
            uint32_t vert_size = vert.size();
            uint32_t idx_size = idx.size();
            mesh.write((char*)&vert_size, 4);
            mesh.write((char*)&idx_size, 4);
            mesh.write((char*)&std::get<1>(offsets[offset]), 2);
            for (unsigned i = 0; i < vert.size(); i++)
            {
                float float_array[4];
                vert[i].m_position.getAs4Values(float_array);
                mesh.write((char*)float_array, 12);
                uint32_t nor;
                uint16_t half_float;
                if (export_normal)
                {
                    vert[i].m_normal.getAs4Values(float_array);
                    mdm_normalNativeTo10_10_10_2(&nor, float_array);
                    mesh.write((char*)&nor, 4);
                }
                if (export_vcolor)
                {
                    if (vert[i].m_color == video::SColor(255, 255, 255, 255))
                    {
                        uint8_t tmp = 128;
                        mesh.write((char*)&tmp, 1);
                    }
                    else
                    {
                        uint8_t tmp = 255;
                        mesh.write((char*)&tmp, 1);
                        tmp = vert[i].m_color.getRed();
                        mesh.write((char*)&tmp, 1);
                        tmp = vert[i].m_color.getGreen();
                        mesh.write((char*)&tmp, 1);
                        tmp = vert[i].m_color.getBlue();
                        mesh.write((char*)&tmp, 1);
                    }
                }
                const bool has_uv_1 = std::get<2>(offsets[offset]);
                const bool has_uv_2 = std::get<3>(offsets[offset]);
                if (has_uv_1)
                {
                    toHalfFloat(&half_float, vert[i].m_uv_one.X);
                    mesh.write((char*)&half_float, 2);
                    toHalfFloat(&half_float, vert[i].m_uv_one.Y);
                    mesh.write((char*)&half_float, 2);
                    if (has_uv_2)
                    {
                        toHalfFloat(&half_float, vert[i].m_uv_two.X);
                        mesh.write((char*)&half_float, 2);
                        toHalfFloat(&half_float, vert[i].m_uv_two.Y);
                        mesh.write((char*)&half_float, 2);
                    }
                    if (export_tangent)
                    {
                        vert[i].m_tangent.getAs4Values(float_array);
                        mdm_normalNativeTo10_10_10_2(&nor, float_array);
                        mesh.write((char*)&nor, 4);
                        vert[i].m_bitangent.getAs4Values(float_array);
                        mdm_normalNativeTo10_10_10_2(&nor, float_array);
                        mesh.write((char*)&nor, 4);
                    }
                }
                if (header == "SPMA")
                {
                    mesh.write((char*)vert[i].m_bone_idx, 8);
                    toHalfFloat(&half_float, vert[i].m_weights[0]);
                    mesh.write((char*)&half_float, 2);
                    toHalfFloat(&half_float, vert[i].m_weights[1]);
                    mesh.write((char*)&half_float, 2);
                    toHalfFloat(&half_float, vert[i].m_weights[2]);
                    mesh.write((char*)&half_float, 2);
                    toHalfFloat(&half_float, vert[i].m_weights[3]);
                    mesh.write((char*)&half_float, 2);
                }
            }
            for (unsigned i = 0; i < idx.size(); i++)
            {
                mesh.write((char*)&idx[i],
                    vert_size > 65535 ? 4 : vert_size > 255 ? 2 : 1);
            }
        }
        if (header == "SPMS")
        {
            writeBBox(mesh, s.second);
        }
    }
    if (header == "SPMA")
    {
        writeArmData(mesh, in_arms);
    }
    else if (header == "SPMS")
    {
        // Reserved for pre-computed visible sectors
        uint16_t pre_computed_size = 0;
        mesh.write((char*)&pre_computed_size, 2);
    }
    return 0;
}
