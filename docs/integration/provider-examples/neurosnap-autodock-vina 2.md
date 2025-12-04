# NeuroSnap AutoDock Vina Submission Example

```python
import json
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

multipart_data = MultipartEncoder(
    fields={
        "Input Receptor": ("structure.pdb", open("structure.pdb", "rb")),
        "Input Ligand": json.dumps([
            {"data": open("receptor.sdf").read(), "type": "sdf"},
            {"data": "C=C=C", "type": "smiles"},
        ]),
        "Scoring Function": "default",
        "Local Only": "false",
        "Score Only": "false",
        "Minimization Iterations": "0",
    }
)

response = requests.post(
    "https://neurosnap.ai/api/job/submit/AutoDock Vina (smina)?note=my job description",
    headers={
        "X-API-KEY": "<YOUR_API_KEY>",
        "Content-Type": multipart_data.content_type,
    },
    data=multipart_data,
)
response.raise_for_status()
print(response.json())
```

> **Tip:** Omit optional fields such as `Local Only` or `Score Only` when the value is `false`; the provider treats their absence as `false`.
