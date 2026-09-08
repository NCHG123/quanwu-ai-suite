# 00 - Knowledge Base Index (for the developer)

这批文档是项目1（RAG知识库问答系统）的语料，模拟一家全屋定制工厂出海后的B2B客户问答场景。

## 业务设定
- 主角：一家中国全屋定制工厂（厨房柜、衣柜、浴室柜、整屋定制），做OEM/ODM出口
- 客户：海外装修公司、房地产开发商、海外全屋定制企业/经销商
- 文档语言：英文（客户是海外B端，RAG要用英文回答客户问题）
- 用途：销售接待Agent / 官网客服 / 询盘问答的知识底座

## 文档清单
| 文件 | 内容 | 对应客户问题类型 |
|---|---|---|
| 01-company-profile | 工厂概况、产能、OEM/ODM能力 | 你是谁、能做什么 |
| 02-materials | 板材类型、甲醛等级、适用场景 | 用什么料、环保等级 |
| 03-finishes-doors | 门板工艺、饰面选择 | 外观、风格 |
| 04-hardware | 铰链、滑轨、五金品牌与参数 | 五金品质 |
| 05-product-categories | 产品线与标准尺寸 | 产品规格 |
| 06-design-production | 从量尺到出货的流程 | 流程、交期 |
| 07-certifications | CARB/FSC/E1/CE等认证 | 合规、准入 |
| 08-shipping-logistics | 包装方式、集装箱、Incoterms | 运输、成本 |
| 09-commercial-terms | MOQ、付款、样品、经销政策 | 商务条款 |
| 10-after-sales | 安装、质保、售后 | 售后 |
| 11-faq-overseas | 海外合作FAQ（小批量/运输/安装/单证，Q&A格式） | 高频咨询，RAG命中率最高 |
| 12-solid-wood | 整木定制线（楼梯/木门/护墙板/酒窖） | 高端项目咨询 |
| 13-product-catalog | SKU规格页样例（含图片位说明） | 型号级查询 |
| 14-communication-guidelines | 对内/对外口径规范（AUDIENCE分级、禁止披露清单、语气规则、转人工条件） | 系统设计：双入口检索的分级依据 |
| 15-pricing-logic-internal | 价格区间、阶梯折扣、成本构成、报价流程（仅内部） | 内部入口：报价类问题 |
| 16-sales-playbook | 异议处理话术、3个匿名案例、USP卖点、跟进节奏 | 对外入口：销售对话 |

**重要：14–16 引入了"AUDIENCE分级"概念。** RAG系统给每个文档/段落打标 `PUBLIC` 或 `INTERNAL`，外部入口检索时过滤掉 INTERNAL 内容——这是本项目的一个亮点设计（检索过滤/权限控制），面试可以展开讲。

## 建议测试问题（验收RAG效果用，挑10个先试）
1. What board materials do you offer and which is best for humid climates?
2. What is the difference between CARB P2 and E1? Which one do I need for the US market?
3. What is your MOQ and payment terms for first-time buyers?
4. How many cabinets fit in a 40HQ container — flat-pack or assembled?
5. What is the production lead time for a 100-unit apartment project?
6. Do you provide FSC-certified materials?
7. Can you ship fully assembled cabinets to Australia?
8. What hardware brands do you use? Can I specify Blum?
9. What is included in your warranty?
10. What documents do you provide for customs clearance?

## 使用方式
把这16个文档复制到你项目里的 docs/ 文件夹，作为RAG的第一批语料。13是SKU规格页模板，以后往真实工厂资料扩展时保持同样的字段结构。

**价格数字说明：** 15号文档里的价格区间是行业合理参考值（可在文件顶部调整），用于让系统跑起来像真的；接真实工厂时替换成实盘数据即可。
