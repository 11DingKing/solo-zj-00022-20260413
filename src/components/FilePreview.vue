<template>
  <b-modal
    :visible="previewVisible"
    size="xl"
    centered
    hide-footer
    no-close-on-backdrop
    @hide="handleClose"
  >
    <template slot="modal-header">
      <div class="preview-header">
        <h5 class="modal-title">{{ (previewData && previewData.filename) || 'File Preview' }}</h5>
        <div class="preview-controls" v-if="previewData && previewData.file_type === 'image'">
          <b-button variant="secondary" size="sm" @click="zoomIn" title="Zoom In">
            <font-awesome-icon icon="search-plus" />
          </b-button>
          <b-button variant="secondary" size="sm" @click="zoomOut" title="Zoom Out">
            <font-awesome-icon icon="search-minus" />
          </b-button>
          <b-button variant="secondary" size="sm" @click="resetZoom" title="Reset">
            <font-awesome-icon icon="sync" />
          </b-button>
        </div>
      </div>
    </template>

    <div class="preview-content">
      <!-- 图片预览 -->
      <div v-if="previewData && previewData.file_type === 'image'" class="image-preview-container">
        <div 
          class="image-wrapper"
          :style="imageWrapperStyle"
          @mousedown="startDrag"
          @mousemove="onDrag"
          @mouseup="stopDrag"
          @mouseleave="stopDrag"
        >
          <img 
            :src="previewData.preview_url" 
            :alt="previewData.filename"
            :style="imageStyle"
            draggable="false"
          />
        </div>
      </div>

      <!-- PDF 预览 -->
      <div v-else-if="previewData && previewData.file_type === 'pdf'" class="pdf-preview-container">
        <iframe 
          :src="previewData.preview_url"
          class="pdf-iframe"
          frameborder="0"
        ></iframe>
      </div>

      <!-- 禁止预览的类型 -->
      <div v-else-if="previewData && previewData.file_type === 'forbidden'" class="unsupported-preview">
        <div class="unsupported-icon">
          <font-awesome-icon icon="exclamation-triangle" size="5x" />
        </div>
        <h4>不支持预览</h4>
        <p>{{ (previewData && previewData.error) || '此文件类型无法预览' }}</p>
      </div>

      <!-- 其他不支持的类型 -->
      <div v-else class="unsupported-preview">
        <div class="unsupported-icon">
          <font-awesome-icon icon="file" size="5x" />
        </div>
        <h4>不支持预览</h4>
        <p>此文件类型暂不支持预览</p>
      </div>
    </div>
  </b-modal>
</template>

<script>
import { mapState, mapActions } from 'vuex'

export default {
  name: 'FilePreview',
  data() {
    return {
      scale: 1,
      positionX: 0,
      positionY: 0,
      isDragging: false,
      lastX: 0,
      lastY: 0
    }
  },
  computed: {
    ...mapState(['previewData', 'previewVisible']),
    imageStyle() {
      return {
        transform: `scale(${this.scale})`,
        transformOrigin: 'center center',
        transition: this.isDragging ? 'none' : 'transform 0.2s ease'
      }
    },
    imageWrapperStyle() {
      return {
        transform: `translate(${this.positionX}px, ${this.positionY}px)`,
        cursor: this.isDragging ? 'grabbing' : 'grab'
      }
    }
  },
  watch: {
    previewVisible(newVal) {
      if (newVal) {
        this.resetZoom()
      }
    }
  },
  methods: {
    ...mapActions(['closePreview']),
    handleClose() {
      this.closePreview()
      this.resetZoom()
    },
    zoomIn() {
      this.scale = Math.min(this.scale + 0.25, 5)
    },
    zoomOut() {
      this.scale = Math.max(this.scale - 0.25, 0.25)
    },
    resetZoom() {
      this.scale = 1
      this.positionX = 0
      this.positionY = 0
    },
    startDrag(e) {
      if (this.scale > 1) {
        this.isDragging = true
        this.lastX = e.clientX
        this.lastY = e.clientY
      }
    },
    onDrag(e) {
      if (this.isDragging) {
        const deltaX = e.clientX - this.lastX
        const deltaY = e.clientY - this.lastY
        this.positionX += deltaX
        this.positionY += deltaY
        this.lastX = e.clientX
        this.lastY = e.clientY
      }
    },
    stopDrag() {
      this.isDragging = false
    }
  }
}
</script>

<style lang="scss" scoped>
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.preview-controls {
  display: flex;
  gap: 5px;
}

.preview-content {
  min-height: 400px;
  max-height: 70vh;
  overflow: hidden;
}

// 图片预览样式
.image-preview-container {
  width: 100%;
  height: 60vh;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.image-wrapper {
  max-width: 100%;
  max-height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  user-select: none;
}

.image-wrapper img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

// PDF 预览样式
.pdf-preview-container {
  width: 100%;
  height: 60vh;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

// 不支持预览的样式
.unsupported-preview {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 60vh;
  text-align: center;
  color: #6c757d;
}

.unsupported-icon {
  margin-bottom: 20px;
  color: #adb5bd;
}

.unsupported-preview h4 {
  margin-bottom: 10px;
  color: #495057;
}

.unsupported-preview p {
  margin: 0;
}
</style>
