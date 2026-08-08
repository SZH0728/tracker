# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 验证上游请求结果的 pytest 契约。
@details 覆盖成功与失败字段的互斥关系，以及已实现的稳定失败类别。
"""

import pytest

from requester import FetchFailureKind, FetchResult


def create_success_result() -> FetchResult:
    """
    @brief 创建有效的成功请求结果。
    @return 符合成功契约的请求结果。
    """
    return FetchResult(
        attempts=1,
        body=b'content',
        content_type='text/plain',
        failure_kind=None,
        failure_message=None,
        final_url='https://example.invalid/final',
        original_url='https://example.invalid/original',
        status_code=200,
    )


def test_fetch_result_identifies_success() -> None:
    """
    @brief 验证完整成功结果可被识别。
    @return 无返回值。
    """
    result = create_success_result()

    assert result.is_success is True
    assert result.body == b'content'


@pytest.mark.parametrize(
    ('overrides', 'exception_type'),
    [
        ({'attempts': 0}, ValueError),
        ({'attempts': '1'}, TypeError),
        ({'body': 'content'}, TypeError),
        ({'failure_kind': FetchFailureKind.NETWORK}, ValueError),
        ({'failure_kind': FetchFailureKind.NETWORK, 'failure_message': '连接失败', 'body': b'content'}, ValueError),
        ({'final_url': None}, ValueError),
    ],
)
def test_fetch_result_rejects_invalid_field_combinations(
    overrides: dict[str, object],
    exception_type: type[Exception],
) -> None:
    """
    @brief 验证无效的成功或失败字段组合会被拒绝。
    @param overrides 要覆盖的结果字段
    @param exception_type 预期异常类别
    @return 无返回值。
    """
    values: dict[str, object] = {
        'attempts': 1,
        'body': b'content',
        'content_type': 'text/plain',
        'failure_kind': None,
        'failure_message': None,
        'final_url': 'https://example.invalid/final',
        'original_url': 'https://example.invalid/original',
        'status_code': 200,
    }
    values.update(overrides)

    with pytest.raises(exception_type):
        FetchResult(**values)  # type: ignore[arg-type]  # 参数化测试表示动态字段覆盖


def test_fetch_failure_kind_uses_stable_protocol_values() -> None:
    """
    @brief 验证失败类别的字符串协议值稳定。
    @return 无返回值。
    """
    assert FetchFailureKind.NETWORK == 'network'
    assert FetchFailureKind.RESPONSE_TOO_LARGE == 'response-too-large'


if __name__ == '__main__':
    pass
