#ifndef __sidefxlabs_data_h__
#define __sidefxlabs_data_h__


// Float to String

string labs_ftoa(const float f; const int decimal_places)
{
    return sprintf("%.*g", decimal_places + (int)log10(abs(f)) + (abs(f) >= 1.0), f);
}

string labs_ftoa(const float f)
{
    return labs_ftoa(f, 3);
}


// Binary Search

float labs_binarysearch(const int array[], target_value; export int success)
{
    success = 0;
    int n = len(array);
    if (n == 0) return -1.0;

    int l = 0;
    int r = n - 1;
    int m = -1;

    while (l <= r)
    {
        m = (l + r) / 2;

        if (array[m] < target_value)
        {
            l = m + 1;
        }
        else if (array[m] > target_value)
        {
            r = m - 1;
        }
        else
        {
            success = 1;
            break;
        }
    }

    // Only happens when the left index is 1 less than the right
    // index and the target value is between the two values
    if (l > r) m = r;

    // If the target value is greater than a few duplicated values
    // but less than the next value, the middle index will always
    // move to the last of the duplicates

    float index = m;

    if (!success)
    {
        if (target_value < array[0] || target_value > array[n - 1])
            index = -1.0;
        else if (m + 1 < n)
            // In VEX, division by zero is allowed. It just returns zero.
            index += float(target_value - array[m]) / (array[m + 1] - array[m]);
    }

    return index;
}

float labs_binarysearch(const float array[], target_value; export int success)
{
    success = 0;
    int n = len(array);
    if (n == 0) return -1.0;

    int l = 0;
    int r = n - 1;
    int m = -1;

    // Forces the target value to have the same floating-point precision as the array elements
    float target_value_safe = set(target_value, 0)[0];

    while (l <= r)
    {
        m = (l + r) / 2;

        if (array[m] < target_value_safe)
        {
            l = m + 1;
        }
        else if (array[m] > target_value_safe)
        {
            r = m - 1;
        }
        else
        {
            success = 1;
            break;
        }
    }

    // Only happens when the left index is 1 less than the right
    // index and the target value is between the two values
    if (l > r) m = r;

    // If the target value is greater than a few duplicated values
    // but less than the next value, the middle index will always
    // move to the last of the duplicates

    float index = m;

    if (!success)
    {
        if (target_value_safe < array[0] || target_value_safe > array[n - 1])
            index = -1.0;
        else if (m + 1 < n)
            // In VEX, division by zero is allowed. It just returns zero.
            index += float(target_value_safe - array[m]) / (array[m + 1] - array[m]);
    }

    return index;
}

int labs_binarysearch(const string array[], target_value; export int success)
{
    success = 0;
    int n = len(array);
    if (n == 0) return -1;

    int l = 0;
    int r = n - 1;
    int m = -1;

    while (l <= r)
    {
        m = (l + r) / 2;

        if (array[m] < target_value)
        {
            l = m + 1;
        }
        else if (array[m] > target_value)
        {
            r = m - 1;
        }
        else
        {
            success = 1;
            break;
        }
    }

    // Only happens when the left index is 1 less than the right
    // index and the target value is between the two values
    if (l > r) m = r;

    // If the target value is greater than a few duplicated values
    // but less than the next value, the middle index will always
    // move to the last of the duplicates

    int index = m;

    if (!success)
    {
        if (target_value < array[0] || target_value > array[n - 1])
            index = -1;
    }

    return index;
}


// Append Unique

void labs_append_unique(export int array[]; const int value)
{
    if (find(array, value) < 0)
        append(array, value);
}

void labs_append_unique(export float array[]; const float value)
{
    if (find(array, value) < 0)
        append(array, value);
}

void labs_append_unique(export vector2 array[]; const vector2 value)
{
    if (find(array, value) < 0)
        append(array, value);
}

void labs_append_unique(export vector array[]; const vector value)
{
    if (find(array, value) < 0)
        append(array, value);
}

void labs_append_unique(export vector4 array[]; const vector4 value)
{
    if (find(array, value) < 0)
        append(array, value);
}

void labs_append_unique(export string array[]; const string value)
{
    if (find(array, value) < 0)
        append(array, value);
}

void labs_append_unique(export string str; const string value)
{
    if (find(str, value) < 0)
        append(str, value);
}


// Make Array Unique

int[] labs_array_unique(const int array[])
{
    int array_unique[] = {};

    foreach (int value; array)
        labs_append_unique(array_unique, value);

    return array_unique;
}

float[] labs_array_unique(const float array[])
{
    float array_unique[] = {};

    foreach (float value; array)
        labs_append_unique(array_unique, value);

    return array_unique;
}

vector2[] labs_array_unique(const vector2 array[])
{
    vector2 array_unique[] = {};

    foreach (vector2 value; array)
        labs_append_unique(array_unique, value);

    return array_unique;
}

vector[] labs_array_unique(const vector array[])
{
    vector array_unique[] = {};

    foreach (vector value; array)
        labs_append_unique(array_unique, value);

    return array_unique;
}

vector4[] labs_array_unique(const vector4 array[])
{
    vector4 array_unique[] = {};

    foreach (vector4 value; array)
        labs_append_unique(array_unique, value);

    return array_unique;
}

string[] labs_array_unique(const string array[])
{
    string array_unique[] = {};

    foreach (string value; array)
        labs_append_unique(array_unique, value);

    return array_unique;
}

string labs_array_unique(const string str)
{
    string str_unique = "";

    foreach (string value; str)
        labs_append_unique(str_unique, value);

    return str_unique;
}


#endif