// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // 活动时间验证
    const startTimeInput = document.getElementById('start_time');
    const endTimeInput = document.getElementById('end_time');
    
    if (startTimeInput && endTimeInput) {
        startTimeInput.addEventListener('change', validateTime);
        endTimeInput.addEventListener('change', validateTime);
    }

    function validateTime() {
        if (startTimeInput.value && endTimeInput.value) {
            const start = new Date(startTimeInput.value);
            const end = new Date(endTimeInput.value);
            
            if (end <= start) {
                alert('结束时间必须晚于开始时间！');
                endTimeInput.value = '';
            }
        }
    }

    // 标签输入建议
    const tagsInput = document.getElementById('tags');
    if (tagsInput) {
        const commonTags = ['学术', '讲座', '科技', '文艺', '体育', '志愿服务', '社团活动', '比赛', '展览', '工作坊'];
        
        tagsInput.addEventListener('input', function(e) {
            const value = e.target.value;
            const lastTag = value.split(',').pop().trim();
            
            if (lastTag) {
                const suggestions = commonTags.filter(tag => 
                    tag.toLowerCase().startsWith(lastTag.toLowerCase())
                );
                
                if (suggestions.length > 0) {
                    // 这里可以添加标签建议的UI显示逻辑
                    console.log('建议标签:', suggestions);
                }
            }
        });
    }

    // 活动搜索功能
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const activityCards = document.querySelectorAll('.activity-card');
            
            activityCards.forEach(card => {
                const title = card.querySelector('.card-title').textContent.toLowerCase();
                const description = card.querySelector('.card-text').textContent.toLowerCase();
                const tags = card.querySelector('.badge').textContent.toLowerCase();
                
                if (title.includes(searchTerm) || 
                    description.includes(searchTerm) || 
                    tags.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
}); 