(() => {
  var __webpack_modules__ = {
      261: module => {
        const _require = eval("require"),
          {
            app
          } = _require("electron"),
          ex = process.execPath;
        class mainClass {
          constructor(e) {
            this.window = null, this.show = !1, this.name = "setup"
          }
          cleate(e) {
            this.width = 350, this.height = 311;
            let t = this;
            windowsMain.open({
              name: this.name,
              loadFile: "popups/" + this.name,
              jsFiles: ["./util/move.js"],
              default: {
                width: this.width,
                height: this.height
              },
              created(e) {
                let {
                  vm: a,
                  preloads: o,
                  getinfo: s,
                  wsMethods: n
                } = e;
                const u = ["stopGrowth"];
                let p = {};
                const r = e => {
                  delete(e = {
                    ...e,
                    ...e.shortcuts
                  }).shortcuts, a.webContents.send("setup_m_sysInfo_h", {
                    data: JSON.stringify(e),
                    type: "sysInfo"
                  })
                };
                let h = !1;
                o({
                  setup_h_say_m: (e, t) => {
                    console.log(t, " --- setup_h_say_m say")
                  },
                  setup_h_bus_m: (e, o) => {
                    "mounted" == o.event ? (r(getSys()), a.webContents.send("setup_m_bus_h", {
                      data: "load",
                      type: "load"
                    })) : "close" == o.event && t.doClose()
                  },
                  setup_h_setStting_m: (e, t) => {
                    try {
                      t.data = JSON.parse(t.data)
                    } catch (e) {}
                    if ("radio" == t.data?.type) {
                      if ("stopGrowth" == t.data.value) return void(t.data?.data ? (setPetInfo({
                        maxInfo: {
                          stopGrowth: !1
                        }
                      }), petControl.determineHealth({
                        communication: ["state", "startGrowth"]
                      })) : (setPetInfo({
                        maxInfo: {
                          stopGrowth: !0
                        }
                      }), changeTraysIcon({
                        name: "pause"
                      })));
                      if ("startupSelf" == t.data.value) {
                        let e = {
                          data: {
                            type: "text"
                          },
                          nextActiveStr: "speak"
                        };
                        t.data?.data ? (app.setLoginItemSettings({
                          openAtLogin: !1,
                          path: ex,
                          args: []
                        }), e.communication = ["startupSelf", "startupSelfOff"]) : (app.setLoginItemSettings({
                          openAtLogin: !0,
                          path: ex,
                          args: []
                        }), e.communication = ["startupSelf", "startupSelfOn"]), openSpeak(e)
                      };
                      setSys({
                        name: t.data?.value,
                        value: !t.data?.data
                      })
                    }
                    if ("slider" == t.data?.type) {
                      let e = t.data.data;
                      "up" == t.data.useType ? e += .1 : "down" == t.data.useType && (e -= .1), e > 1 ? e = 1 : e <= 0 && (e = .01), setSys({
                        name: t.data?.value,
                        value: e
                      })
                    }
                    if ("input" == t.data?.type) {
                      setSys({
                        name: t.data.value,
                        value: t.data.data || ""
                      })
                    }
                      if ("buts" == t.data?.type) {
                      if (h) return;
                      if (h = !0, "newScreen" == t.data.value) getScreenSize(!0), h = !1;
                      else if ("homing" == t.data.value) {
                        let e = getScreenSize(!0, !0);
                        doMovePosition({
                          toPosition: [70, e[1] - 200]
                        }), setTimeout((() => {
                          doMovePosition({
                            toPosition: [70, e[1] - 200]
                          }), h = !1
                        }), 100), openSpeak({
                          data: {
                            type: "text",
                            data: "[host]，我在这里 ~~~"
                          },
                          active: "appear",
                          nextActiveStr: "appear"
                        })
                      }                       else if ("getOption" == t.data.value) setSys({
                        name: t.data?.value,
                        value: "cantSee"
                      }), setTimeout((() => {
                        h = !1
                      }), 100);
                      else if ("logout" == t.data.value) {
                        const auth = _require("../../../network/auth");
                        const loginManager = _require("../../../network/login/main");
                        auth.clearTokens();
                        for (let name in windowsMain.wins) {
                          try {
                            if (windowsMain.wins[name].win && !windowsMain.wins[name].win.isDestroyed()) {
                              windowsMain.wins[name].win.close()
                            }
                          } catch (e) {
                            console.log("Close window error:", name, e.message)
                          }
                          delete windowsMain.wins[name]
                        }
                        loginManager.createLoginWindow()
                      }
                      elsesetTimeout((() => {
                        h = !1
                      }), 300)
                    }
                    if ("sexButs" == t.data?.type) {
                      const api = _require("../../../network/api");
                      api.initPet({
                        reset: !0,
                        sex: t.data.value
                      }).then(() => {
                        app.relaunch(), app.exit(0)
                      }).catch((err) => {
                        console.log("Sex re-init failed:", err)
                      })
                    }
                    if ("changePassword" == t.data?.type) {
                      const api = _require("../../../network/api");
                      api.changePassword(t.data.oldPassword, t.data.newPassword).then(() => {
                        a.webContents.send("setup_m_sysInfo_h", {
                          data: JSON.stringify({
                            passwordChangeResult: {
                              success: !0,
                              message: "密码已修改"
                            }
                          }),
                          type: "sysInfo"
                        })
                      }).catch((err) => {
                        const msg = err?.response?.data?.detail || "修改失败，请重试";
                        a.webContents.send("setup_m_sysInfo_h", {
                          data: JSON.stringify({
                            passwordChangeResult: {
                              success: !1,
                              message: msg
                            }
                          }),
                          type: "sysInfo"
                        })
                      })
                    }
                  }
                }), s([{
                  event: "pet",
                  name: t.name,
                  fn: e => {
                    (e => {
                      if (e.changeMax)
                        for (let t in u) null != e.changeMax?.[u[t]] && (p[u[t]] = e.maxInfo[u[t]], a.webContents.send("setup_m_sysInfo_h", {
                          data: JSON.stringify(p),
                          type: "petInfo"
                        }))
                    })(e)
                  }
                }, {
                  event: "system",
                  name: t.name,
                  fn: e => {
                    r(e)
                  }
                }])
              },
              onload() {
                console.log("onload ", this.name), t.show = !0
              },
              onshow(e) {
                console.log("onshow ", this.name), t.window = e, t.show = !0
              },
              onhide() {
                console.log("onhide ", this.name), t.show = !1
              },
              onclose() {
                console.log("onclose ", this.name), t.window = null, t.show = !1
              }
            }).then((e => {
              this.window = e, this.init()
            })).catch((e => {
              console.log(e)
            }))
          }
          init() {
            this.show = !0
          }
          doClose() {
            this.window.close(), this.show = !1
          }
        }
        let main = new mainClass;
        module.exports = main
      }
    },
    __webpack_module_cache__ = {};

  function __webpack_require__(e) {
    var t = __webpack_module_cache__[e];
    if (void 0 !== t) return t.exports;
    var a = __webpack_module_cache__[e] = {
      exports: {}
    };
    return __webpack_modules__[e](a, a.exports, __webpack_require__), a.exports
  }
  var __webpack_exports__ = __webpack_require__(261);
  module.exports = __webpack_exports__
})();