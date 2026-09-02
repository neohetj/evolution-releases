# Evolution 发布仓库

本仓库统一管理 Evolution 二进制的发布编排与不可变分发元数据。
组件源码仍保留在各自的私有仓库中；二进制以 GitHub Release Asset 发布，不提交为 Git blob。

## 已发布组件

| 组件 | 源码仓库 | 构建目标 |
| --- | --- | --- |
| `operator` | `neohetj/operator` | `make release` |
| `keymaker-runner-step` | `neohetj/keymaker` | `make release-runner-step` |

每个组件拥有独立的语义版本和 Release Tag，例如 `operator-v1.4.2`。
`runner-bundle-v<version>` 会冻结两个组件的一组兼容版本。
经过评审的 `channels/runner-stable.json` 是唯一可变的 stable 指针。

## 发布流程

1. 手动触发 `Publish component`，填写组件、版本、精确的 40 位组件源码 commit 和 Matrix
   依赖 commit。
2. 工作流检出组件及 Matrix 的精确私有仓库 commit，执行源码仓库定义的交叉构建，校验组件
   清单，为每个产物生成来源证明，并创建新的不可变组件 Release。
3. 使用两个已经发布的组件版本触发 `Publish Runner bundle`。
4. 触发 `Promote Runner channel`；工作流会创建 PR，将不可变的 Bundle 清单复制到 `channels/runner-stable.json`。

仓库 Secret `RELEASE_SOURCE_TOKEN` 必须是 fine-grained token 或 GitHub App token，且只拥有
`neohetj/operator`、`neohetj/keymaker` 和 `neohetj/matrix` 的 Contents 只读权限。该 Token
不拥有本仓库的写权限；创建 Release 时使用当前工作流权限受限的 `GITHUB_TOKEN`。

首次生产发布前必须启用 GitHub immutable releases。不得使用覆盖 Asset 的参数，也不得复用已发布的组件或 Bundle 版本。

## 消费地址

Keymaker 应使用经过评审的 stable channel：

```text
https://raw.githubusercontent.com/neohetj/evolution-releases/main/channels/runner-stable.json
```

生产环境也可以直接固定到某个不可变 Bundle 清单的 Asset URL。

## 本地验证

```bash
make check
python3 scripts/release_contract.py validate-component \
  --component operator /path/to/component-manifest.json
python3 scripts/release_contract.py validate-bundle /path/to/runner-bundle-manifest.json
```
