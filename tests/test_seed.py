from ftmq.model import Dataset

from investigraph.logic.seed import handle
from investigraph.model import Config, Source
from investigraph.model.context import DatasetContext, SourceContext
from investigraph.model.stage import SeedStage


def test_seed(fixtures_path):
    dataset = Dataset(name="test")
    uri = str(fixtures_path)
    glob = "*.json"
    seed = SeedStage(uri=uri, glob=glob)
    config = Config(dataset=dataset, seed=seed)
    ctx = DatasetContext(config=config)
    res = [x for x in handle(ctx)]
    assert len(res) == 1
    assert isinstance(res[0], Source)
    ctx = SourceContext(config=config, source=res[0])
    with ctx.open() as fh:
        assert fh.read()

    # empty
    config = Config(dataset=dataset)
    ctx = DatasetContext(config=config)
    res = [x for x in handle(ctx)]
    assert len(res) == 0
