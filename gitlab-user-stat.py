import gitlab
import json
import time

# 读取配置文件
with open('./config.json', 'r', encoding='utf8')as fp:
    config = json.load(fp)

# 配置默认值
if "debug" not in config:
    config["debug"] = False
if "start_time" not in config:
    # 开始时间默认当月初
    day_now = time.localtime()
    config["start_time"] = '%d-%02d-01' % (day_now.tm_year, day_now.tm_mon)
if "alias" not in config:
    config["alias"] = {}

# gitlab 客户端初始化
client = gitlab.Gitlab(config["gitlab_url"],
                       private_token=config["private_token"], timeout=5, api_version='4')
client.auth()

# 用户统计信息dict
user_stats = {}

# 处理所有工程
for proj_name in config["project"]:
    print('project processing: {}'.format(proj_name))
    # 获取工程
    try:
        pro = client.projects.get(proj_name)
        if config["debug"]:
            print(pro)
        # 获取提交
        commits = pro.commits.list(all=True, since=config["start_time"])
        for c in commits:
            if config["debug"]:
                print('commit:{}'.format(c))
            # 忽略分支合并提交
            if ('Merge branch' in c.message) and ('into' in c.message):
                if config["debug"]:
                    print('skip merge commit:{},{}'.format(c.short_id, c.title))
            else:
                # 获取提交详细信息， 并针对用户统计
                comm = pro.commits.get(c.id)
                if comm.author_name in user_stats:
                    user_stats[comm.author_name] = user_stats[comm.author_name] + \
                        comm.stats['additions']
                else:
                    user_stats[comm.author_name] = comm.stats['additions']
    except Exception as e:
        print('Error: {}, {}'.format(proj_name, e))

# 输出用户统计
print('commit line count:')
for user in user_stats.keys():
    alias = user
    # 获取用户别名
    if user in config["alias"]:
        alias = config["alias"][user]
    # 输出用户统计信息
    print('{}\t{}'.format(alias, user_stats[user]))
