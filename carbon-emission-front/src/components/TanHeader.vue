<template>
  <div class="total">
    <div class="header">
      <div class="header-content">
        <div class="carbonleft">
          <div class="logo-container">
            <img :src="logoUrl" alt="北京林业大学" class="system-logo" @error="handleImageError">
          </div>
          <div class="title-container">
            <div class="title-main">北京林业大学</div>
            <div class="title-sub">BJFU</div>
          </div>
        </div>
        <div class="right">
          <div class="system-title">碳排放核算与管理系统</div>
        <el-menu router class="tan-el-menu" mode="horizontal">
          <el-menu-item index="/Tan/TanPage" class="header-icon el-icon-s-home" style="font-size: 20px;">
            首页</el-menu-item>
          <el-submenu index="1">
            <template slot="title">
              <i class="header-icon el-icon-s-data"></i>
              <span>数据输入</span>
            </template>
            <el-menu-item-group>
              <el-menu-item index="/Tan/ManageSchool" class="el-icon-school"
                style="font-size: 16px;">&nbsp;&nbsp;学校信息</el-menu-item>
              <el-menu-item index="/Tan/ManagePlace" class="el-icon-location"
                style="font-size: 16px;">&nbsp;&nbsp;排放地点</el-menu-item>
              <el-menu-item index="/Tan/ExchangeSetting" class="el-icon-location"
                style="font-size: 16px;">&nbsp;&nbsp;碳排放转化系数</el-menu-item>
              <el-menu-item @click="jumpCarbon()" class="el-icon-location"
                style="font-size: 16px;">&nbsp;&nbsp;碳排放记录</el-menu-item>
            </el-menu-item-group>
          </el-submenu>

          <el-submenu index="2">
            <template slot="title">
              <i class="header-icon el-icon-s-flag"></i>
              <span>能耗监测</span>
            </template>
            <el-menu-item-group>
              <el-menu-item index="/Tan/TanMonitor" class="el-icon-location"
                style="font-size: 16px;">&nbsp;&nbsp;能耗碳排放监测</el-menu-item>
              <el-menu-item index="/Tan/TanAudit" class="el-icon-location"
                style="font-size: 16px;">&nbsp;&nbsp;能耗碳排放审计</el-menu-item>
              <el-menu-item index="/Tan/TanContrast" class="el-icon-location"
                style="font-size: 16px;">&nbsp;&nbsp;能耗碳排放对比</el-menu-item>
            </el-menu-item-group>
          </el-submenu>

          <el-submenu index="3">
            <template slot="title">
              <i class="header-icon el-icon-s-data"></i>
              <span>碳排放计算与减碳分析</span>
            </template>
            <el-menu-item-group>
              <el-menu-item index="/Tan/TanResult" class="el-icon-location"
                style="font-size: 16px;">&nbsp;&nbsp;流动趋势</el-menu-item>
              <el-menu-item index="/Tan/TanAnalyse" class="el-icon-location"
                style="font-size: 16px;">&nbsp;&nbsp;减碳分析</el-menu-item>
            </el-menu-item-group>
          </el-submenu>

          <el-menu-item index="/Tan/TanExport" class="header-icon el-icon-s-order"
            style="font-size: 20px;">报告生成</el-menu-item>

          <el-submenu index="4">
            <template slot="title">
              <i class="header-icon el-icon-setting"></i>
              <span style="font-size: 20px;">系统管理</span>
            </template>
            <el-menu-item-group>
              <el-menu-item index="/Tan/ManageUser" class="el-icon-user"
                style="font-size: 16px;">&nbsp;&nbsp;用户管理</el-menu-item>
              <el-menu-item index="/Tan/ManageRole" class="el-icon-s-custom"
                style="font-size: 16px;">&nbsp;&nbsp;角色管理</el-menu-item>
              <el-menu-item index="/Tan/ManagePermission" class="el-icon-key"
                style="font-size: 16px;">&nbsp;&nbsp;权限管理</el-menu-item>
            </el-menu-item-group>
          </el-submenu>

          <div class="avatar">
            <el-dropdown @command="handleCommand" placement="bottom" trigger="hover" popper-class="user-dropdown-menu">
              <span class="user-img-icon">
                <i class="el-icon-user-solid"></i>
              </span>
              <el-dropdown-menu slot="dropdown">
                <el-dropdown-item v-if="isLogin === 'youke'" command="login">登录</el-dropdown-item>
                <el-dropdown-item v-else command="signout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </el-dropdown>
          </div>

        </el-menu>
        </div>
      </div>
    </div>
    <div class="child">
      <router-view></router-view>
    </div>
  </div>
</template>

<script>
import pubsub from 'pubsub-js'
import { logoutApi } from '../api/user'
import tokenManager from '../utils/tokenManager'

export default {
  name: 'TanHeader',
  data() {
    return {
      loginForm: false,
      isLogin: 'youke',
      logoUrl: require('../assets/bjfu-logo.png')
    }
  },
  props: {
  },
  created() {
    this.$bus.$on('updateLoginStatus', (data) => {
      this.isLogin = data
    })
    this.checkLoginStatus()
  },
  watch: {
    '$route'() {
      this.checkLoginStatus()
    }
  },
  methods: {
    checkLoginStatus() {
      const token = tokenManager.getAccessToken()
      const auth = localStorage.getItem('auth')
      if (token && auth) {
        this.isLogin = auth
      } else {
        this.isLogin = 'youke'
      }
    },
    async handleCommand(command) {
      if (command == 'signout') {
        try {
          await logoutApi()
        } catch (error) {
          console.error('Logout API error:', error)
        }
        tokenManager.clearTokens()
        localStorage.removeItem("userId")
        localStorage.removeItem("auth")
        this.$message.success('退出登录成功')
        this.isLogin = 'youke'
        this.$bus.$emit('updateLoginStatus', 'youke')
        this.$router.push({ path: '/Tan/TanPage' })
      } else if (command == 'login') {
        this.$router.push({ path: '/Tan/TanLogin' })
      } else if (command == 'backtoindex') {
        this.$router.push({ path: '/Tan/adminPage' })
      }
    },
    jumpCarbon() {
      this.$router.push({
        path: 'ManageCarbon',
      });
    },
    handleImageError(e) {
      console.error('Logo图片加载失败:', e);
      if (e.target && e.target.parentElement) {
        e.target.parentElement.style.display = 'none';
      }
    },
    jump(value) {
      this.$router.push({
        name: 'TanLogin',
      })
    }
  },

  beforeDestroy() {
  }
}
</script>

<style scoped>
.total {
  padding: 0;
  width: 100%;
}

.header {
  white-space: nowrap;
  position: fixed;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #4a7c3a 0%, #2d5016 100%);
  height: 80px;
  width: 100%;
  top: 0px;
  left: 0;
  z-index: 1000;
  padding: 0 40px;
  box-sizing: border-box;
  box-shadow: 0 2px 12px rgba(45, 80, 22, 0.15);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  max-width: 1600px;
  gap: 20px;
}

.carbonleft {
  display: inline-block;
  margin-left: 0;
  margin-right: 0;
  flex-shrink: 0;
  display: flex !important;
  align-items: center !important;
  height: 80px !important;
  gap: 12px !important;
  width: auto !important;
  min-width: 0 !important;
  max-width: none !important;
  padding-right: 15px !important;
}

.logo-container {
  flex-shrink: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 56px !important;
  height: 56px !important;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, rgba(255, 255, 255, 0.1) 100%) !important;
  border: 2px solid rgba(255, 255, 255, 0.3) !important;
  border-radius: 12px !important;
  padding: 8px !important;
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  backdrop-filter: blur(4px) !important;
}

.system-logo {
  width: 100% !important;
  height: 100% !important;
  object-fit: contain !important;
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.25)) !important;
  transition: filter 0.3s ease !important;
  display: block !important;
}

.title-container {
  flex: 0 0 auto !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  gap: 4px !important;
  min-width: 0 !important;
  position: relative !important;
  white-space: nowrap !important;
}

.title-main {
  font-size: 22px !important;
  font-weight: 600 !important;
  color: #FFFFFF !important;
  line-height: 1.3 !important;
  letter-spacing: 0.5px !important;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  font-family: "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Arial, sans-serif !important;
}

.title-sub {
  font-size: 24px !important;
  font-weight: 700 !important;
  color: #FFFFFF !important;
  line-height: 1.2 !important;
  letter-spacing: 8px !important;
  text-shadow:
    0 2px 4px rgba(0, 0, 0, 0.3),
    0 4px 8px rgba(0, 0, 0, 0.2),
    0 0 10px rgba(255, 255, 255, 0.1) !important;
  white-space: nowrap !important;
  font-family: "Arial", "Helvetica Neue", sans-serif !important;
  text-transform: uppercase !important;
}

.right {
  white-space: nowrap;
  height: 80px;
  flex: 1;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 25px;
  padding-left: 20px;
}

.system-title {
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif !important;
  font-size: 24px !important;
  font-weight: 700 !important;
  letter-spacing: 2px !important;
  line-height: 1.4 !important;
  white-space: nowrap !important;
  padding: 0 15px 0 0 !important;
  background: linear-gradient(to bottom, #f0f9eb 0%, #ffffff 50%, #b8d9a8 100%) !important;
  -webkit-background-clip: text !important;
  background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  color: transparent !important;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3)) !important;
}

.child {
  margin-top: 80px;
  text-align: left;
  width: 100%;
  min-height: calc(100vh - 80px);
  background-color: var(--forest-bg-primary);
}
</style>

