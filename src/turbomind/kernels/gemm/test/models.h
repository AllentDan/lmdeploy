// Copyright (c) OpenMMLab. All rights reserved.

#pragma once

#include <cstdint>
#include <utility>
#include <vector>

static const std::vector<std::pair<int64_t, int64_t>> config{
    {11008 * 2, 4096}, {4096, 11008}, {12288, 4096}, {4096, 4096},  // llama2-7b
    {14336 * 2, 4096}, {4096, 14336}, {6144, 4096},  {4096, 4096},  // llama3-8b / internlm2.5-7b
    {16384 * 2, 6144}, {6144, 16384}, {8192, 6144},  {6144, 6144},  // internlm2-20b
    {13696 * 2, 4096}, {4096, 13696}, {4608, 4096},  {4096, 4096},  // glm4-9b
    {18944 * 2, 3584}, {3584, 18944}, {4608, 3584},  {3584, 3584},  // qwen2-7b
    {20480 * 2, 7168}, {7168, 20480}, {9216, 7168},  {7168, 7168},  // yi-34b
    {28672 * 2, 8192}, {8192, 28672}, {10240, 8192}, {8192, 8192},  // llama2-70b / llama3-70b
    {29696 * 2, 8192}, {8192, 29696}, {10240, 8192}, {8192, 8192}   // qwen2-72b-instruct-awq
};
// {29568 * 2, 8192}, {8192, 29568}, {10240, 8192}, {8192, 8192},  // qwen2-72b
