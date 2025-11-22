# 简易通用爬虫
通过使用配置文件适配多数网站

## 使用方法
1. 安装依赖`pip install -r requirements.txt`
2. 修改配置文件
3. 执行index.py `python .\index.py .\${配置文件名}.json`
4. 等待执行完毕

## 配置文件说明
```json
{
    // 配置文件标识符目前没什么用
    "name": "mooc", 
    // 要爬取的网址
    "url": "https://www.icourse163.org/course/ZJU-199001",
    // 预操作（例课程页面默认不显示评论要点击评论按钮切换tab页后才显示）
    // 非必须字段
    "preop": {
        // 根据css获取要进行操作的元素
        "css": "#review-tag-button", // 必须
        "sample_url":true, // 相同链接是否终止，有些网站下一页按钮常显，有些网页不是通过url参数切换网页
        // 避免第二种情况自动停止
        // 对元素进行的操作（目前没用）
        "op": "click"
    },
    // 页面规则
    // 有该规则则会按多页逻辑进行处理
    // 没有则按单页逻辑处理
    "page": {
        // 下一页按钮的css
        "css": ".ux-pager_btn__next", // 必须
        // 对下一页进行的操作（目前没用）
        "op": "click",
        // 最大页数
        "max":150 // 可选
    },
    // 页面处理规则即要获取哪些内容
    "rules": {
        // 自定义
        "class_info": {
            "type": "one", // 必须
            "only_one": true, // 非必须 是否只获取一次
            // 同下方list类型
            // 具体内容
            "targets": [
                {
                    // 关键字字段
                    // 定义输出文件中保存的字段名
                    // 必须
                    "kw": "title",
                    // 该元素的css选择器
                    // 必须
                    "css": ".course-title",
                    // 获取的数据是txt还是元素属性
                    // 必须
                    "loc": "txt",
                    // 对获取的内容进行处理
                    // 只有上方loc为txt才会进行处理
                    "parse": {
                        // 处理方式
                        // 目前只支持截取 slice
                        "type": "slice",
                        // 起始位置
                        "start": 2,
                        // 结束位置
                        "end":-4
                    }
                }
            ]
        },
        "content": {
            // 类型list则会获取同css规则的所有元素
            // 类型one则只获取一个元素
            "type": "list", // 必须 one or list
            // css这里类名不用加.
            "css": "ux-mooc-comment-course-comment_comment-list_item", // 必须
            // 列表类型才有用对获取的元素列表进行截取有些元素包含无用信息
            // 必须
            "start": 0,
            "end": 0,
            // 具体内容
            "targets": [
                {
                    // 关键字字段
                    // 定义输出文件中保存的字段名
                    // 必须
                    "kw": "author",
                    // 该元素的css选择器
                    // 必须
                    "css": ".ux-mooc-comment-course-comment_comment-list_item_body_user-info a:first-child",
                    // 获取的数据是txt还是元素属性
                    // 必须
                    "loc": "txt", // txt or attr
                    // 可选
                    "attrs":[
                        {
                            "kw":"src",// 必须
                            "type":"byte",// 必须 byte or txt
                            "pre":"http:", // 可选有些src的链接不全需要加前缀
                            "save_type":""// 保存的文件后缀名 例png
                        }
                    ],
                }
                // ...
            ],
        }
    },
    // 输出配置
    // 用于定义输出文件相关内容
    // 必须
    "output": {
        // 输出的文件目录即文件夹名
        "name": "mooc", // 必须
        // 输出的文件格式 目前只适配了json
        "format": "json", // 必须
        // 输出的文件编码
        "encoding": "utf-8" // 必须
    },
    // 非必须
    // 改变显示输出的内容 default or debug
    "log-level":"default"
}
```