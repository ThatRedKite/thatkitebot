#include <stdio.h>
#include <math.h>
#include <Python.h>

// store info for quick change
#define _version "Version 1.0"

// store a few essential variables as a macro
#define ipc_exp1    1.37931034483f
#define ipc_exp2    0.725f
#define ipc_exp3    0.440f

// standard jlcpcb offers
#define jlc_standard_1      1.37795276f     // jlc 1 oz copper layer
#define jlc_standard_2      2.75590551f     // jlc 2 oz copper layer
#define jlc_standard_int    0.688976378f    // jlc internal copper layer

// C functions

/*
 *  implementing a function to calculate the desired pcb trace width according to IPC 2221
 *  the user provides the maximum current, the max desired temperature rise, length and whenever its internal or not
 */
float _width(float current, float delta_temp, float thickness, int internal)
{
    float K = (internal == 0) ? 0.048f : 0.024f;  // give out the correct K variable depending on if the trace is internal or external
    float H = (internal == 0) ? jlc_standard_1 : jlc_standard_int;   // give out the H variable depending on if the trace is internal or external
    float thicc = (thickness == 0) ? H : thickness;     // incase this value is 0, choose the default value H instead of user given value thickness
    float temp = (delta_temp == 0) ? 10 : delta_temp;   // if user does not select a temperature, assume 10°C

    return powf((current / (K * powf(temp, ipc_exp3))), ipc_exp1) / thicc;
}

/*
 *  this function will return the maximum current a trace can handle
 */
float _current(float temp_delta, float width, float thickness, int internal)
{
    float K = (internal == 0) ? 0.048f : 0.024f;  // give out the correct K variable depending on if the trace is internal or external
    float H = (internal == 0) ? jlc_standard_1 : jlc_standard_int;   // give out the H variable depending on if the trace is internal or external
    float thicc = (thickness == 0) ? H : thickness;     // incase this value is 0, choose the default value H instead of user given value thickness
    float temp = (delta_temp == 0) ? 10 : delta_temp;   // if user does not select a temperature, assume 10°C

    return K * powf(temp, ipc_exp3) * powf((width * thicc), ipc_exp2);
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
    {"mm2mil", mm2mil, METH_VARARGS, "Converts millimeters to mils"},
    {"mil2mm", mil2mm, METH_VARARGS, "Converts mils to millimeters"},
    {"weight2mil", weight2mil, METH_VARARGS, "Converts oz/fl2 to mils"},
    {"version", (PyCFunction)version, METH_NOARGS, "returns the current version."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef pcb_mod = {
    PyModuleDef_HEAD_INIT,
    "pcb_mod",
    "PCB related calculators",
    -1,
    pcb_meth
};

PyMODINIT_FUNC PyInit_pcb_mod(void)
{
    return PyModule_Create(&pcb_mod);
}