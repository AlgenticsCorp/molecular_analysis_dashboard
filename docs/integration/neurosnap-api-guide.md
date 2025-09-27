# NeuroSnap API Integration Guide

## 🎯 Overview

This document provides comprehensive guidance for integrating with the NeuroSnap API, specifically for GNINA molecular docking. This guide addresses the format discrepancies between NeuroSnap's general documentation and their actual GNINA implementation.

## ⚠️ **CRITICAL: API Format Differences**

### **❌ Incorrect Format (from general docs)**
```python
# This format DOES NOT WORK for GNINA
fields = {
    "Input Receptor": json.dumps([{"type": "pdb", "data": receptor_data}]),
    "Input Ligand": json.dumps([{"type": "sdf", "data": ligand_data}])
}
```

### **✅ Correct Working Format for GNINA**
```python
# This format WORKS for GNINA
fields = {
    # Receptor: tuple format (filename, binary_data)
    "Input Receptor": (filename, open(receptor_file, "rb")),
    # Ligand: JSON with data BEFORE type
    "Input Ligand": json.dumps([{"data": ligand_data, "type": "sdf"}])
}
```

## 🔧 **Implementation Details**

### **Key Differences Discovered:**

1. **Receptor Format**:
   - ❌ **Wrong**: JSON serialization with type/data objects
   - ✅ **Correct**: Tuple format `(filename, binary_file_handle)`

2. **Ligand Format**:
   - ❌ **Wrong**: Field order `{"type": "sdf", "data": ligand_data}`
   - ✅ **Correct**: Field order `{"data": ligand_data, "type": "sdf"}`

3. **File Handling**:
   - ❌ **Wrong**: Text decoding of receptor files
   - ✅ **Correct**: Binary handling for receptor files

### **Working Implementation Examples**

#### **FastAPI Endpoint (API Implementation)**
```python
async def call_neurosnap(receptor_file: UploadFile, ligand_file: UploadFile, note: str) -> str:
    # Read receptor as binary
    receptor_content = await receptor_file.read()
    ligand_content = await ligand_file.read()

    # Decode ligand as text
    ligand_data = ligand_content.decode("utf-8")

    # Use correct format
    fields = {
        "Input Receptor": (receptor_file.filename or "structure.pdb", receptor_content),
        "Input Ligand": json.dumps([{"data": ligand_data, "type": "sdf"}])
    }

    multipart_data = MultipartEncoder(fields=fields)

    response = requests.post(
        f"https://neurosnap.ai/api/job/submit/GNINA?note={note}",
        headers={"X-API-KEY": get_api_key(), "Content-Type": multipart_data.content_type},
        data=multipart_data,
        timeout=30,
    )

    return response.json()
```

#### **Notebook Script Implementation**
```python
def submit_gnina_job(receptor_file, ligand_file=None, job_note="GNINA docking job"):
    API_KEY = os.getenv("NEUROSNAP_API_KEY")

    fields = {}

    # Receptor: tuple format
    fields["Input Receptor"] = (os.path.basename(receptor_file), open(receptor_file, "rb"))

    # Ligand: JSON format with data first
    if ligand_file and os.path.exists(ligand_file):
        with open(ligand_file, 'r') as f:
            ligand_data = f.read()
        fields["Input Ligand"] = json.dumps([{"data": ligand_data, "type": "sdf"}])

    multipart_data = MultipartEncoder(fields=fields)

    response = requests.post(
        f"https://neurosnap.ai/api/job/submit/GNINA?note={job_note}",
        headers={"X-API-KEY": API_KEY, "Content-Type": multipart_data.content_type},
        data=multipart_data
    )

    return response.json()
```

## 🧪 **Testing & Validation**

### **Successful Test Results**
- **API Endpoint**: Returns job ID `68d8615c545d2bb25a34dc95`
- **Status Code**: 200 (Success)
- **Response Format**: JSON string containing job ID

### **Test Files Used**
- **Receptor**: `test_receptor.pdb` (79 bytes)
- **Ligand**: `test_ligand.sdf` (70 chars)

## 🔍 **Troubleshooting**

### **Common Issues & Solutions**

#### **"Input Receptor was not provided" Error**
- **Cause**: Using JSON format instead of tuple format for receptor
- **Solution**: Use `(filename, binary_data)` tuple format

#### **"Input Ligand was not provided" Error**
- **Cause**: Wrong field order in JSON (type before data)
- **Solution**: Use `{"data": content, "type": "sdf"}` order

#### **UnicodeDecodeError**
- **Cause**: Trying to decode binary receptor data as UTF-8
- **Solution**: Handle receptor as binary, only decode ligand data

### **Debug Tips**

```python
# Add debug logging to verify format
print(f"DEBUG: Receptor format: {type(fields['Input Receptor'])}")
print(f"DEBUG: Ligand format: {fields['Input Ligand'][:100]}...")

# Verify multipart structure
multipart_body = multipart_data.read()
body_str = multipart_body.decode('utf-8', errors='ignore')
field_patterns = re.findall(r'name="([^"]*)"', body_str)
print(f"DEBUG: Found field names: {field_patterns}")
```

## 🚀 **Integration Checklist**

- [ ] **API Key**: NeuroSnap API key configured in environment
- [ ] **Dependencies**: `requests-toolbelt` and `python-multipart` installed
- [ ] **Format**: Using correct tuple format for receptor
- [ ] **Field Order**: Ligand JSON has data before type
- [ ] **File Handling**: Receptor as binary, ligand as text
- [ ] **Error Handling**: Proper timeout and exception handling
- [ ] **Testing**: Verified with actual molecular data

## 📋 **Service Information**

### **GNINA Service Details**
- **Resource Cost**: 0.00025 credits per job
- **Runtime**: ~37 seconds average
- **Input Requirements**:
  - **Receptor**: PDB format, 10-5000 residues
  - **Ligand**: SDF format, 2-400 atoms

### **API Endpoints Used**
- **Job Submission**: `POST https://neurosnap.ai/api/job/submit/GNINA`
- **Status Check**: `GET https://neurosnap.ai/api/job/status/{job_id}`
- **File Download**: `GET https://neurosnap.ai/api/job/file/{job_id}/out/{filename}`

## 🔗 **Related Documentation**

- [NeuroSnap Official Blog](https://neurosnap.ai/blog/post/66b00dacec3f2aa9b4be703a)
- [GNINA Publication](https://jcheminf.biomedcentral.com/articles/10.1186/s13321-021-00522-2)
- [Project API Implementation](../src/molecular_analysis_dashboard/presentation/api/routes/docking.py)
- [Notebook Integration](../temp/scripts/submit_gnina_job.py)

---

*Last Updated: September 27, 2025*
*Status: ✅ Working Implementation Verified*
