#include <stdio.h>
#include <math.h>
#include <Python.h>

// store info for quick change
#define _version "Version 1.1"

// store a few essential variables as a macro
#define ipc_exp1    1.37931034483f
#define ipc_exp2    0.725f
#define ipc_exp3    0.440f

// standard jlcpcb offers
#define jlc_standard_1      1.37795276f     // jlc 1 oz copper layer
#define jlc_standard_2      2.75590551f     // jlc 2 oz copper layer
#define jlc_standard_int    0.688976378f    // jlc internal copper layer

// standard jlcpcb dielectrics
#define die_const_7628  4.60f
#define die_const_2313  4.05f
#define die_const_2116  4.25f

// standard e series values
#define _eseries        1, 3, 6, 12, 24, 48, 96, 192

// these are pre defined to avoid heavy math
#define _e1     1.0
#define _e3     1.0, 2.2, 4.7
#define _e6     1.0, 1.5, 2.2, 3.3, 4.7, 6.8
#define _e12    1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2
#define _e24    1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1
#define _e48    1.00, 1.05, 1.10, 1.15, 1.21, 1.27, 1.33, 1.40, 1.47, 1.54, 1.62, 1.69, 1.78, 1.87, 1.96, 2.05, 2.15, 2.26, 2.37, 2.49, 2.61,\
                2.74, 2.87, 3.01, 3.16, 3.32, 3.48, 3.65, 3.83, 4.02, 4.22, 4.42, 4.64, 4.87, 5.11, 5.36, 5.62, 5.90, 6.19, 6.49, 6.81, 7.15,\
                7.50, 7.87, 8.25, 8.66, 9.09, 9.53
#define _e96    1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30, 1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58, 1.62,\
                1.65, 1.69, 1.74, 1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10, 2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55, 2.61, 2.67,\
                2.74, 2.80, 2.87, 2.94, 3.01, 3.09, 3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12, 4.22, 4.32, 4.42,\
                4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49, 5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15, 7.32,\
                7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76
#define _e192   1.00, 1.01, 1.02, 1.04, 1.05, 1.06, 1.07, 1.09, 1.10, 1.11, 1.13, 1.14, 1.15, 1.17, 1.18, 1.20, 1.21, 1.23, 1.24, 1.26, 1.27,\
                1.29, 1.30, 1.32, 1.33, 1.35, 1.37, 1.38, 1.40, 1.42, 1.43, 1.45, 1.47, 1.49, 1.50, 1.52, 1.54, 1.56, 1.58, 1.60, 1.62, 1.64,\
                1.65, 1.67, 1.69, 1.72, 1.74, 1.76, 1.78, 1.80, 1.82, 1.84, 1.87, 1.89, 1.91, 1.93, 1.96, 1.98, 2.00, 2.03, 2.05, 2.08, 2.10,\
                2.13, 2.15, 2.18, 2.21, 2.23, 2.26, 2.29, 2.32, 2.34, 2.37, 2.40, 2.43, 2.46, 2.49, 2.52, 2.55, 2.58, 2.61, 2.64, 2.67, 2.71,\
                2.74, 2.77, 2.80, 2.84, 2.87, 2.91, 2.94, 2.98, 3.01, 3.05, 3.09, 3.12, 3.16, 3.20, 3.24, 3.28, 3.32, 3.36, 3.40, 3.44, 3.48,\
                3.52, 3.57, 3.61, 3.65, 3.70, 3.74, 3.79, 3.83, 3.88, 3.92, 3.97, 4.02, 4.07, 4.12, 4.17, 4.22, 4.27, 4.32, 4.37, 4.42, 4.48,\
                4.53, 4.59, 4.64, 4.70, 4.75, 4.81, 4.87, 4.93, 4.99, 5.05, 5.11, 5.17, 5.23, 5.30, 5.36, 5.42, 5.49, 5.56, 5.62, 5.69, 5.76,\
                5.83, 5.90, 5.97, 6.04, 6.12, 6.19, 6.26, 6.34, 6.42, 6.49, 6.57, 6.65, 6.73, 6.81, 6.90, 6.98, 7.06, 7.15, 7.23, 7.32, 7.41,\
                7.50, 7.59, 7.68, 7.77, 7.87, 7.96, 8.06, 8.16, 8.25, 8.35, 8.45, 8.56, 8.66, 8.76, 8.87, 8.98, 9.09, 9.20, 9.31, 9.42, 9.53,\
                9.65, 9.76, 9.88


static int _valid_series[] = { _eseries };

static float _eseries_arr[8][192] = {
    { _e1 },
    { _e3 },
    { _e6 },
    { _e12 },
    { _e24 },
    { _e48 },
    { _e96 },
    { _e192 }
};


// implementing a function to calculate the desired pcb trace width according to IPC 2221
float _width(float current, float temp_delta, float thickness, int internal)
{
    float K = (internal == 0) ? 0.048f : 0.024f;  // give out the correct K variable depending on if the trace is internal or external
    float H = (internal == 0) ? jlc_standard_1 : jlc_standard_int;   // give out the H variable depending on if the trace is internal or external
    float thicc = (thickness == 0) ? H : thickness;     // incase this value is 0, choose the default value H instead of user given value thickness
    float temp = (temp_delta == 0) ? 10 : temp_delta;   // if user does not select a temperature, assume 10°C

    return powf((current / (K * powf(temp, ipc_exp3))), ipc_exp1) / thicc;
}


// this function will return the maximum current a trace can handle
float _current(float temp_delta, float width, float thickness, int internal)
{
    float K = (internal == 0) ? 0.048f : 0.024f;  // give out the correct K variable depending on if the trace is internal or external
    float H = (internal == 0) ? jlc_standard_1 : jlc_standard_int;   // give out the H variable depending on if the trace is internal or external
    float thicc = (thickness == 0) ? H : thickness;     // incase this value is 0, choose the default value H instead of user given value thickness
    float temp = (temp_delta == 0) ? 10 : temp_delta;   // if user does not select a temperature, assume 10°C

    return K * powf(temp, ipc_exp3) * powf((width * thicc), ipc_exp2);
}


// impedance calculator for pcb microtraces
//float _impedance(float space, float width, float cu_thicc, float iso_thicc, float die_const, int microstrip)
//{
//    return 0;
//}


// check if the user input e series is an accepted series and returns 1, returns 0 if it fails
int _check_series(int series)
{
    int arr_size = sizeof(_valid_series) / sizeof(int);

    // check if user input is a real series
    for(int i = 0; i < arr_size; i++)
    {
        if(_valid_series[i] == series)
            return 1;
    }

    // since the loop failed, the series doesnt exist
    return 0;
}


// get array index
int _get_index(int arr[], int size, int value)
{
    int index = 0;

    while (index < size && arr[index] != value) 
        ++index;
    
    return index == size ? -1 : index;
}


// find the closest E series resistor to the desired value 
float _eseries_resistor(float resistor, int series)
{
    float ans = 0;
    float mantissa, verify;
    int arr_id, exponent;

    // checks if resistor input is valid, else return 0
    if(resistor <= 0)
        return 0;

    // checks if series is a real series, if not, return 0
    if(_check_series(series) == 0)
        return 0;

    // get the output in scientific notation
    exponent = (int) log10(resistor);
    mantissa = resistor / pow(10, exponent);
    arr_id = _get_index(_valid_series, (sizeof(_valid_series) / sizeof(int)), series);

    // find the nearest value in the selected e series
    verify = _eseries_arr[arr_id][series - 1];

    for(int i = 0; i < series; i++)
    {
        //printf("checking: %.2f against %.2f, verify showing: %.2f, best so far: %.2f\n", _eseries_arr[arr_id][i], mantissa, verify, ans);

        if(fabs(_eseries_arr[arr_id][i] - mantissa) < verify)
        {
            verify = fabs(_eseries_arr[arr_id][i] - mantissa);
            ans = _eseries_arr[arr_id][i];
        }
        else if(fabs(_eseries_arr[arr_id][i] - mantissa) > verify)
            break;
    }

    return (ans * pow(10, exponent));
}


// get the percentage delta
float _eseries_error(float resistor, float closest_resistor)
{
    return ((closest_resistor / resistor) - 1) * 100;
}


// convert millimeters to mils
float _mm2mil(float mm)
{
    return mm / 0.0254;
}


// convert mils to millimeters
float _mil2mm(float mil)
{
    return 0.0254 * mil;
}


// convert copper weight oz/fl2 to mil
float _weight2mil(float weight)
{
    return weight * jlc_standard_1;
}


// Python garbage

static PyObject* width(PyObject* self, PyObject* args)
{
    float current, delta_temp, thickness;
    int internal;

    if(!PyArg_ParseTuple(args, "fffi", &current, &delta_temp, &thickness, &internal))
        return NULL;

    return Py_BuildValue("f", _width(current, delta_temp, thickness, internal));
}


static PyObject* current(PyObject* self, PyObject* args)
{
    float temp_delta, width, thickness;
    int internal;

    if(!PyArg_ParseTuple(args, "fffi", &temp_delta, &width, &thickness, &internal))
        return NULL;

    return Py_BuildValue("f", _current(temp_delta, width, thickness, internal));
}


//static PyObject* impedance(PyObject* self, PyObject* args)
//{
//    return 0;
//}


static PyObject* check_series(PyObject* self, PyObject* args)
{
    int series;
    
    if(!PyArg_ParseTuple(args, "i", &series))
        return NULL;

    return Py_BuildValue("i", _check_series(series)); 
}


static PyObject* e_resistor(PyObject* self, PyObject* args)
{
    float resistor;
    int series;
    
    if(!PyArg_ParseTuple(args, "fi", &resistor, &series))
        return NULL;

    return Py_BuildValue("f", _eseries_resistor(resistor, series)); 
}


static PyObject* e_error(PyObject* self, PyObject* args)
{
    float resistor, closest_resistor;
    
    if(!PyArg_ParseTuple(args, "ff", &resistor, &closest_resistor))
        return NULL;

    return Py_BuildValue("f", _eseries_error(resistor, closest_resistor)); 
}


static PyObject* mm2mil(PyObject* self, PyObject* args)
{
    float mm;

    if(!PyArg_ParseTuple(args, "f", &mm))
        return NULL;

    return Py_BuildValue("f", _mm2mil(mm));    
}


static PyObject* mil2mm(PyObject* self, PyObject* args)
{
    float mil;

    if(!PyArg_ParseTuple(args, "f", &mil))
        return NULL;

    return Py_BuildValue("f", _mil2mm(mil));    
}


static PyObject* weight2mil(PyObject* self, PyObject* args)
{
    float weight;

    if(!PyArg_ParseTuple(args, "f", &weight))
        return NULL;

    return Py_BuildValue("f", _weight2mil(weight));    
}


static PyObject* version(PyObject* self)
{
    return Py_BuildValue("s", _version);
}


static PyMethodDef pcb_meth[] = {
    {"width", width, METH_VARARGS, "Calculates the necessary trace width."},
    {"current", current, METH_VARARGS, "Calculates the maximum current."},
    //{"impedance", impedance, METH_VARARGS, "Finds the microstrip impedance of a PCB microstrip."},
    {"check_series", check_series, METH_VARARGS, "Checks if the E series is real"},
    {"e_resistor", e_resistor, METH_VARARGS, "Finds the closest E series resistor, supports E1 through E192"},
    {"e_error", e_error, METH_VARARGS, "Gets the difference between the user provided resistor, and the closest E series resistor"},
    {"mm2mil", mm2mil, METH_VARARGS, "Converts millimeters to mils"},
    {"mil2mm", mil2mm, METH_VARARGS, "Converts mils to millimeters"},
    {"weight2mil", weight2mil, METH_VARARGS, "Converts oz/fl2 to mils"},
    {"version", (PyCFunction)version, METH_NOARGS, "returns the current version."},
    {NULL, NULL, 0, NULL}
};


static struct PyModuleDef pcb_mod = {
    PyModuleDef_HEAD_INIT,
    "pcb_mod",
    "Electronics related calculators",
    -1,
    pcb_meth
};


PyMODINIT_FUNC PyInit_pcb_mod(void)
{
    return PyModule_Create(&pcb_mod);
}