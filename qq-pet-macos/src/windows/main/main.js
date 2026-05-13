(() => {
  var __webpack_modules__ = {
      953: module => {
        const _require = eval("require"),
          {
            app,
            screen
          } = _require("electron"),
          {
            myPet
          } = _require("../util/pet/petIndex"),
          {
            MenuCreate
          } = _require("./menu");
        global.petControl = new myPet;
        const stateInfo = _require("../popups/stateInfo/main.js"),
          control = _require("../popups/control/main.js"),
          tip = _require("../popups/tip/main.js");
        let saveSpeakData = null;
        global.openSpeak = e => {
          saveSpeakData = e
        };
        const rightMenu = _require("../popups/rightMenu/main.js"),
          {
            getCommunication
          } = _require("../util/pet/communication");
        _require("./Notification.js");
        class mainClass {
          constructor(e) {
            this.window = null, this.show = !1, this.name = "main", this.menu = null, this.loadTime = {
              seeControlTime: null
            }
          }
          reLoad = !0;
          cleate(e) {
            let {
              web: t,
              defaultPetInfo: o
            } = e;
            this.maxSize = [180, 180], this.nowPosition = [0, 0], this.width = this.maxSize[0], this.height = this.maxSize[1];
            let n = this,
              i = null;
            this.bd = !0, this.wellClose = !1, this.petState = "";
            let a = {};
            this.bd ? a.jsFiles = ["./util/move.js", "./util/pet/swfPet.js", "../service/websocket.js"] : a.url = `http://${t.host}:${t.post}/${t.fileName}/windows/main/indexOnline.html`, windowsMain.open({
              name: this.name,
              ...a,
              default: {
                width: this.width || getScreenSize()[0],
                height: this.height || getScreenSize()[1]
              },
              created(e) {
                let {
                  vm: t,
                  preloads: a,
                  getinfo: s,
                  wsMethods: l
                } = e;
                n.nowPosition = t.getPosition();
                let c = {
                  food: "eat",
                  commodity: "clean",
                  medicine: "cure"
                };
                global.changeTraysIcon = e => {
                  let {
                    name: t = null,
                    time: o = null,
                    change: a = !1
                  } = e;
                  n.menu?.activeTraysIcon ? n.menu?.activeTraysIcon({
                    name: t,
                    time: o,
                    change: a
                  }) : i = {
                    name: t,
                    time: o,
                    change: a
                  }
                }, petControl.init({
                  petInfo: getPetInfo(),
                  fn: {
                    backState: (e = {}) => {
                      let {
                        type: t,
                        msg: o,
                        val: n,
                        speak: i,
                        speakType: a,
                        otherData: s,
                        active: l = null,
                        communication: c = null,
                        change: r = !1
                      } = e;
                      i && (o || c) && openSpeak({
                        data: {
                          type: a || "text",
                          data: o || "",
                          ...s || {}
                        },
                        active: l || "speak",
                        nextActiveStr: "speak,sick,hungry,dirty",
                        communication: c || null
                      }), changeTraysIcon({
                        name: t,
                        change: r
                      })
                    },
                    backActive: (e = {}) => {
                      if (setSay("backActive :>> ", e), e.msg || e.communication) {
                        let t = c?.[e.type] || e.type,
                          o = "";
                        "cure" == t && ("ill" == e.overType ? t = "sick" : "dead" == e.overType ? t = "die" : "dead" == e.illType ? (t = "revival", o = "revival") : "err" == e.overType && (t = "speak", o = "speak")), openSpeak({
                          data: {
                            type: "text",
                            data: e.msg,
                            finish: "revival" == t
                          },
                          active: t,
                          communication: e.communication || null,
                          nextActiveStr: o
                        })
                      } else t.webContents.send("main_bus-html_active", {
                        active: c?.[e.type] || e.type
                      })
                    }
                  }
                }), global.setSay = function(...e) {
                  let o = ["↓↓↓↓↓↓↓↓↓↓↓" + tool.getTime()];
                  for (let e in arguments) o.push(arguments[e]);
                  o.push("↑↑↑↑↑↑↑↑↑↑"), t.webContents.send("main_bus-html_setSay", JSON.stringify(o))
                }, global.doMovePosition = e => {
                  if (e?.toPosition) e.maxSize = n.maxSize, n.nowPosition = e?.toPosition;
                  else {
                    n.nowPosition = [n.nowPosition[0] - e.next[0], n.nowPosition[1] - e.next[1]];
                    let t = e.next;
                    for (let o in n.nowPosition) n.nowPosition[o] <= 0 ? (n.nowPosition[o] = 0, t[o] = 0) : n.nowPosition[o] >= getScreenSize()[o] - e.maxSize[0] && (n.nowPosition[o] = getScreenSize()[o] - e.maxSize[0], t[o] = 0)
                  }
                  let o = {
                    x: +n.nowPosition[0],
                    y: +n.nowPosition[1],
                    height: 144,
                    width: 144
                  };
                  var i, a;
                  e.notChangeSize || (n.maxSize = e.maxSize, o = {
                    ...o,
                    height: e.maxSize[1],
                    width: e.maxSize[0]
                  }), t.setBounds(o), i = n.nowPosition, a = getScreenSize(), tip.show && tip.setPosition({
                    position: i,
                    maxSize: n.maxSize
                  }), n.isStop() || (control?.isCleate ? control.setPosition({
                    position: i,
                    screenData: a,
                    maxSize: n.maxSize
                  }) : control.cleate({
                    position: i,
                    screenData: a,
                    maxSize: n.maxSize
                  }, t), t.webContents.send("main_bus-html_setPotision", i, a))
                };
                let r = [n.nowPosition[0] - +o.info.lastX, n.nowPosition[1] - +o.info.lastY];
                doMovePosition({
                  next: r,
                  maxSize: n.maxSize
                }), app.on("before-quit", (e => {
                  if (!n.wellClose) {
                    n.wellClose = !0, e.preventDefault(), setOutProjectMain(!0), setSys({
                      name: "doNotDisturb",
                      value: !1
                    }), $Store.saveLastPosition(n.nowPosition[0], n.nowPosition[1]), setPetInfo({
                      info: {
                        lastX: n.nowPosition[0],
                        lastY: n.nowPosition[1]
                      }
                    }), setTimeout((() => {
                      try {
                        app.exit(0)
                      } catch (e) {}
                    }), 5e3), n.menu?.activeTraysIcon && n.menu?.activeTraysIcon({
                      name: "leave",
                      change: !0
                    }), n.menu?.setTrayToolTip && n.menu?.setTrayToolTip("正在退出···");
                    for (let e in windowsMain.wins)
                      if ("main" != e && windowsMain.wins[e]?.win?.close) try {
                        windowsMain.wins[e].win.close()
                      } catch (e) {}
                    openSpeak({
                      data: {
                        type: "text",
                        load: "exit",
                        finish: "exit"
                      },
                      communication: ["state", "exit"],
                      active: "exit",
                      nextActiveStr: "exit"
                    })
                  }
                })), app.on("second-instance", (() => {
                  if (!n.isStop()) try {
                    openSpeak({
                      data: {
                        type: "text",
                        data: "[host]，我在这里 ~~~"
                      },
                      active: "appear",
                      nextActiveStr: "appear"
                    }), setTimeout((() => {
                      n.appear()
                    }), 80)
                  } catch (e) {
                    setTimeout((() => {
                      app.quit()
                    }), 500)
                  }
                })), a({
                  "html_set-say": (e, t) => {
                    mylog(t, " --- html_set-say say")
                  },
                  "html_bus-Main": (e, o) => {
                    if ("mounted" == o.event) {
                      petControl.startGrowUp();
                      if (typeof focusGuard !== "undefined" && focusGuard?.start) focusGuard.start();
                      let e = getPetInfo();
                      t.webContents.send("main_bus-html", {
                        data: "load",
                        type: "load",
                        screenSize: n.screenSize,
                        nowPosition: n.nowPosition,
                        maxSize: n.maxSize,
                        petInfo: e,
                        bd: n.bd
                      }), n.menu?.setTrayToolTip(e.info.host + "家的" + e.info.name), global.nextActive = e => {
                        t.webContents.send("main_m_nextActive_h", {
                          data: JSON.stringify(e)
                        })
                      };
                      global.openSpeak = e => {
                        let {
                          data: o,
                          active: n,
                          type: i,
                          nextActiveStr: a = "",
                          communication: s = null,
                          otherOpt: l = null
                        } = e;
                        if (!getSys("doNotDisturb") || o?.mustSpeak) {
                          if (("text" == o.type || "seeTextImgs" == o.type) && "object" == typeof s && s?.length > 0) {
                            let _rec = getCommunication(...s);
                            _rec?.tolk && (o.data = _rec.tolk, o.submitText = _rec?.submitText || "")
                          }
                          t.webContents.send("main_bus-html_active", {
                            active: n || "speak",
                            type: i || "speak",
                            load: o.load ? JSON.stringify(o?.load?.msg || o) : !o.finish && JSON.stringify(o),
                            finish: o.finish && JSON.stringify(o),
                            otherOpt: l
                          }), a && nextActive({
                            name: a
                          })
                        }
                      }, saveSpeakData && (openSpeak(saveSpeakData), saveSpeakData = null), t.on("blur", (e => {
                        control.show && control?.changeState("hide")
                      })), n.reLoad && clearTimeout(n.reLoad), n.reLoad = setTimeout((() => {
                        n.reLoad = !1
                      }), 2e3);
                      let o = (e, t, o) => {
                        n.openSpeak({
                          data: {
                            type: "text",
                            data: e,
                            submitText: t,
                            form: "clip"
                          },
                          otherOpt: {
                            type: "click",
                            fn: () => {
                              o && o()
                            }
                          }
                        })
                      };
                    } else "close" == o.event && n.close()
                  },
                  "html_bus-main_move": (e, t) => {
                    doMovePosition(t)
                  },
                  "html_bus-main_getFocus": (e, t) => {},
                  "html_bus-main_mouse": (e, t) => {
                    if (!n.isStop())
                      if ("which" == t.type) {
                        if (control.show && t?.data?.isDown) {
                          if (("normal" == n.petState || "sick" == n.petState) && getPetInfoOne("health", "info") && getChance(.2)) {
                            let e = getRandom(5, 20);
                            e < 1e3 && (e = +getPetInfoOne("mood", "info") + e, e > 1e3 && (e = 1e3), setPetInfo({
                              info: {
                                mood: e
                              }
                            }), openSpeak({
                              data: {
                                type: "text"
                              },
                              communication: ["toHeartTolk"],
                              nextActiveStr: "speak"
                            }))
                          }
                          control.changeState({
                            type: "menu"
                          })
                        }
                      } else if ("rightClick" == t.type) rightMenu.show ? rightMenu.doClose() : rightMenu.cleate({
                      nowPosition: [n.nowPosition[0] + t.data.clientX, n.nowPosition[1] + t.data.clientY],
                      msg: "msg fo rightMenu is rightClick",
                      positionType: "followMain"
                    });
                    else if ("roller" == t.type && (console.log(t, n.petState), "normal" == n.petState || "sick" == n.petState) && getPetInfoOne("health", "info") && getChance(.2)) {
                      let e = getRandom(5, 20);
                      e < 1e3 && (e = +getPetInfoOne("mood", "info") + e, e > 1e3 && (e = 1e3), setPetInfo({
                        info: {
                          mood: e
                        }
                      }), openSpeak({
                        data: {
                          type: "text"
                        },
                        communication: ["toHeartTolk"],
                        nextActiveStr: "speak"
                      }))
                    }
                  },
                  "html_bus-main_backPetLoadFinish": (e, t) => {
                    let o = t.data;
                    try {
                      o = JSON.parse(o)
                    } catch (e) {}
                    "finish" != t.event || "exit" != o && "exit" != o?.finish ? getSys("doNotDisturb") && !o?.mustSpeak || "speak" == t.type && o && n.openSpeak({
                      data: o,
                      otherOpt: t?.otherOpt || null
                    }) : app.exit(0)
                  },
                  main_h_setPetState_m: (e, t) => {
                    try {
                      t.data = JSON.parse(t.data)
                    } catch (e) {}
                    if (n.petState = t?.data?.name || "loadIng", t.data?.tolkName) {
                      const _tn = t.data.tolkName;
                      const _emit = (rec) => {
                        if (!rec) return;
                        t.data?.tolkActive ? openSpeak({
                          data: {
                            type: "text",
                            data: rec.tolk || "出错了~~~",
                            submitText: rec.submitText || ""
                          },
                          active: t?.data?.tolkActive || "",
                          otherOpt: "speak" == t.data?.tolkActive && "smallTalk" == _tn ? {
                            mood: getRandom(5, 20)
                          } : ""
                        }) : n.openSpeak({
                          data: {
                            type: "text",
                            data: rec.tolk || "出错了~~~",
                            submitText: rec.submitText || ""
                          },
                          mustUnShow: !0
                        })
                      };
                      _emit(getCommunication(_tn || ""))
                    }
                  }
                }), petControl?.changePetInfoReply && petControl.changePetInfoReply(getPetInfo()), s([{
                  event: "pet",
                  name: n.name,
                  fn: e => {
                    n.isStop() || (t.webContents.send("main_bus-html_setPet", e), petControl?.changePetInfoReply && petControl.changePetInfoReply(e), e?.changeInfo && ((e?.changeInfo?.host || e?.changeInfo?.name) && n.menu?.setTrayToolTip(e.info.host + "家的" + e.info.name), e?.changeInfo?.addmood && t.webContents.send("main_m_setFloat_h", {
                      type: "seeFloat",
                      data: {
                        num: e.changeInfo.addmood,
                        time: 800
                      }
                    })))
                  }
                }, {
                  event: "system",
                  name: n.name,
                  fn: e => {
                    if (e?.isCHange?.label) {
                      let t = "";
                      "doNotDisturb" == e.isCHange.label && (t = e.isCHange.value ? getCommunication("sys", "doNotDisturbOFF") : getCommunication("sys", "doNotDisturbNO")), t && openSpeak({
                        data: {
                          type: "text",
                          data: t?.tolk || "",
                          submitText: t?.submitText || "",
                          mustSpeak: !0
                        },
                        nextActiveStr: "speak"
                      })
                    }
                  }
                }])
              },
              onload(e) {
                console.log("onload ", this.name), n.menu = new MenuCreate;
                let t = [{
                  on: "click",
                  Fn: e => {
                    n.isStop() || (stateInfo.show ? stateInfo.doClose() : stateInfo.cleate({
                      nowPosition: [e.bounds.x, e.bounds.y],
                      msg: "msg fo stateInfo"
                    }))
                  }
                }, {
                  on: "right-click",
                  Fn: e => {
                    n.isStop() || (rightMenu.show ? rightMenu.doClose() : rightMenu.cleate({
                      nowPosition: [e.bounds.x, e.bounds.y],
                      msg: "msg fo rightMenu is trays"
                    }))
                  }
                }];
                n.menu.addTrays(t), n.menu?.activeTraysIcon && i && n.menu?.activeTraysIcon(i), i && (i = null);
              },
              onshow(e) {
                console.log("onshow ", this.name), n.window = e, n.show = !0
              },
              onhide() {
                console.log("onhide ", this.name), n.show = !1
              },
              onclose() {
                console.log("onclose ", this.name);
                n.menu && n.menu.destroyTray && n.menu.destroyTray();
                n.window = null;
                n.show = !1;
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
            this.window.close(), this.window = null, this.show = !1
          }
          openSpeak(e) {
            let {
              data: t,
              mustUnShow: o,
              otherOpt: n
            } = e;
            if (tip.show) {
              if (o) return;
              tip.setMsg({
                data: t,
                otherOpt: n
              })
            } else tip.cleate({
              position: this.nowPosition,
              maxSize: this.maxSize,
              data: t,
              otherOpt: n
            })
          }
          isStop() {
            return this.wellClose
          }
          appear() {
            !this.show && this.window.show(), !this.window.isAlwaysOnTop() && this.window.setAlwaysOnTop(!0), this.show = !0
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
    var o = __webpack_module_cache__[e] = {
      exports: {}
    };
    return __webpack_modules__[e](o, o.exports, __webpack_require__), o.exports
  }
  var __webpack_exports__ = __webpack_require__(953);
  module.exports = __webpack_exports__
})();