import pytest

from molecular_analysis_dashboard.adapters.providers.neurosnap_task_adapter import (
    NeuroSnapFoldingAdapterBase,
)


class _DummyFoldingAdapter(NeuroSnapFoldingAdapterBase):
    async def submit_task(self, execution, task_definition):
        raise NotImplementedError


@pytest.fixture()
def folding_adapter() -> NeuroSnapFoldingAdapterBase:
    return _DummyFoldingAdapter("Test Service", "Test Job")


@pytest.mark.parametrize(
    "input_value,expected",
    [
        (
            '[{"name": "chainA", "sequence": "ACDE", "type": "aa"}]',
            {"aa": {"chainA": "ACDE"}},
        ),
        (
            ">chainB\nACGT\n",
            {"dna": {"chainB": "ACGT"}},
        ),
        (
            "mktayia",  # simple raw sequence without FASTA header
            {"aa": {"sequence_1": "MKTAYIA"}},
        ),
        (
            ">chainC\nacgu\n",
            {"rna": {"chainC": "ACGU"}},
        ),
    ],
)
def test_parse_sequences_accepts_json_and_fasta(folding_adapter, input_value, expected):
    params = {"sequences": input_value}
    payload = folding_adapter._parse_sequences(params)
    assert payload == expected


def test_parse_sequences_rejects_empty_input(folding_adapter):
    params = {"sequences": ""}
    with pytest.raises(RuntimeError):
        folding_adapter._parse_sequences(params)
