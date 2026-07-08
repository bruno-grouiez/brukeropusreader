from typing import List

from brukeropusreader.block_data import BlockMeta, UnknownBlockType
from brukeropusreader.constants import (
    HEADER_LEN,
    FIRST_CURSOR_POSITION,
    META_BLOCK_SIZE,
)
from brukeropusreader.opus_data import OpusData
from brukeropusreader.opus_reader import (
    read_data_type,
    read_channel_type,
    read_text_type,
    read_chunk_size,
    read_offset,
)


def read_file(file_path: str) -> OpusData:
    with open(file_path, "rb") as opus_file:
        data = opus_file.read()
    meta_data = parse_meta(data)
    opus_data = parse_data(data, meta_data, block_names=None)
    return opus_data

def read_blocks(file_path: str, block_names: List[str]) -> OpusData:
    """
    Read only the requested OPUS blocks.

    Parameters
    ----------
    file_path : str
        Path to the OPUS file.

    block_names : list[str]
        Names of the blocks to decode.

    Returns
    -------
    OpusData
        Dictionary containing only the requested blocks.
    """
    with open(file_path, "rb") as opus_file:
        data = opus_file.read()

    meta_data = parse_meta(data)

    return parse_data(
        data,
        meta_data,
        block_names=block_names,
    )


def parse_meta(data: bytes) -> List[BlockMeta]:
    header = data[:HEADER_LEN]
    spectra_meta = []
    cursor = FIRST_CURSOR_POSITION
    while True:
        if cursor + META_BLOCK_SIZE > HEADER_LEN:
            break

        data_type = read_data_type(header, cursor)
        channel_type = read_channel_type(header, cursor)
        text_type = read_text_type(header, cursor)
        chunk_size = read_chunk_size(header, cursor)
        offset = read_offset(header, cursor)

        if offset <= 0:
            break

        block_meta = BlockMeta(data_type, channel_type,
                               text_type, chunk_size, offset)

        spectra_meta.append(block_meta)

        next_offset = offset + 4 * chunk_size
        if next_offset >= len(data):
            break
        cursor += META_BLOCK_SIZE
    return spectra_meta


def parse_data(data: bytes, blocks_meta: List[BlockMeta], block_names: List[str] = None,) -> OpusData:
    opus_data = OpusData()

    for block_meta in blocks_meta:
        try:
            name, parser = block_meta.get_name_and_parser()
        except UnknownBlockType:
            continue

        # Parse asked block only
        if block_names is not None and name not in block_names:
            continue

        parsed_data = parser(data, block_meta)
        opus_data[name] = parsed_data

    return opus_data