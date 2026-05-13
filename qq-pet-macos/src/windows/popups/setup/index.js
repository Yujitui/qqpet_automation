(() => {
  var e = {},
    t = e => {
      window.electronAPI.setup_h_bus(e)
    };
  const s = {
    data: () => ({
      leftMenu: [{
        label: "全局设置",
        value: "globalSettings",
        children: [{
          label: "透明度",
          type: "slider",
          value: "opacity"
        }, {
          label: "开机自启",
          type: "radio",
          value: "startupSelf"
        }, {
          label: "暂停成长",
          type: "radio",
          value: "stopGrowth"
        }, {
          label: "免打扰模式",
          type: "radio",
          value: "doNotDisturb"
        }]
      }, {
        label: "实用功能",
        value: "utility",
        children: [{
          label: "多屏检测",
          type: "buts",
          value: "newScreen"
        }, {
          label: "宠物归巢",
          type: "buts",
          value: "homing"
        }, {
          label: "性别切换",
          type: "sexButs",
          value: "sex"
        }]
      }, {
        label: "用户管理",
        value: "userManage",
        children: [{
          label: "修改密码",
          type: "passwordForm",
          value: "changePassword"
        }, {
          label: "注销登录",
          type: "buts",
          value: "logout"
        }]
      }, {
        label: "专注守护",
        value: "focusGuard",
        children: [{
          label: "启用专注守护",
          type: "radio",
          value: "focusEnabled"
        }, {
          label: "专注/护眼提醒（25分钟）",
          type: "radio",
          value: "focusEyeReminder"
        }, {
          label: "久坐提醒（50分钟）",
          type: "radio",
          value: "focusSedentaryReminder"
        }, {
          label: "深夜劝睡（22点后）",
          type: "radio",
          value: "focusLateNightReminder"
        }, {
          label: "长时间未操作回归问候",
          type: "radio",
          value: "focusWelcomeBack"
        }]
      }],
      activeMenu: -1,
      seeChildren: [],
      isChangeSysData: {},
      sysData: {
        doNotDisturb: !1,
        stopGrowth: !1,
        opacity: 1,
        focusEnabled: !1,
        focusEyeReminder: !0,
        focusSedentaryReminder: !0,
        focusLateNightReminder: !0,
        focusWelcomeBack: !0
      },
      oldPassword: "",
      newPassword: "",
      passwordBtnText: "确认修改"
    }),
    computed: {},
    created() {},
    mounted() {
      this.chooseMenu(0), window.electronAPI.setup_m_bus(((e, t) => {
        "load" == t.type ? (console.log("load"), seeApp()) : void 0
      })), window.electronAPI.setup_m_sysInfo(((e, t) => {
        let s = t.data;
        try {
          s = JSON.parse(s)
        } catch (e) {}
        if (s.passwordChangeResult) {
          const result = s.passwordChangeResult;
          this.passwordBtnText = result.success ? "✓ 修改成功" : "✗ " + result.message;
          setTimeout(() => {
            this.passwordBtnText = "确认修改"
          }, 3000)
        }
        for (let e in s) this.sysData[e] = s[e]
      })), t({
        event: "mounted"
      })
    },
    methods: {
      setSex(e) {
        window.electronAPI.setup_h_setStting({
          data: JSON.stringify({
            type: "sexButs",
            value: e
          })
        })
      },
      submitChangePassword() {
        if (!this.oldPassword || !this.newPassword) {
          this.passwordBtnText = "请输入密码";
          return
        }
        this.passwordBtnText = "修改中...";
        window.electronAPI.setup_h_setStting({
          data: JSON.stringify({
            type: "changePassword",
            oldPassword: this.oldPassword,
            newPassword: this.newPassword
          })
        })
      },
      setStting(e, t) {
        e = {
          ...e,
          data: this.sysData[e.value]
        }, t && (e.useType = t), "buts" == e.type && "getOption" == e.value ? this.getInputSrc({
          fn: t => {
            e.src = t, window.electronAPI.setup_h_setStting({
              data: JSON.stringify(e)
            })
          }
        }) : window.electronAPI.setup_h_setStting({
          data: JSON.stringify(e)
        })
      },
      getInputSrc(e) {
        let {
          fn: t
        } = e, s = document.createElement("input");
        s.setAttribute("type", "file"), s.setAttribute("webkitdirectory", "true"), s.setAttribute("multiple", ""), s.setAttribute("accept", ".epk"), s.addEventListener("change", (function(e) {
          var a = this.files[0].path;
          t(a), s.remove()
        })), document.body.appendChild(s), s.click()
      },
      chooseMenu(e) {
        this.activeMenu != e && (this.activeMenu = e, this.seeChildren = this.leftMenu[this.activeMenu]?.children || [])
      },
      closeWindow() {
        t({
          event: "close"
        })
      }
    }
  };
  Vue.createApp(s).mount("#app");
  var a = window;
  for (var l in e) a[l] = e[l];
  e.__esModule && Object.defineProperty(a, "__esModule", {
    value: !0
  })
})();